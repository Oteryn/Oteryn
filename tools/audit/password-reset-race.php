<?php
/** Isolated characterization probe; no provider source modification or live data. */
declare(strict_types=1);

const SOURCE_SHA = 'de917b3477a1de0667531380de3660e8b2ab59aa';
const SOURCE_TREE = 'ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e';

function check(bool $condition, string $message): void {
    if (!$condition) { throw new RuntimeException($message); }
}
function command(array $args, string $cwd): string {
    $p = proc_open($args, [0 => ['pipe','r'], 1 => ['pipe','w'], 2 => ['pipe','w']], $pipes, $cwd);
    check(is_resource($p), 'process unavailable'); fclose($pipes[0]);
    $out = stream_get_contents($pipes[1]); $err = stream_get_contents($pipes[2]);
    fclose($pipes[1]); fclose($pipes[2]);
    check(proc_close($p) === 0, 'source identity command failed');
    return trim($out);
}
function boot(string $root, string $database): object {
    check(preg_match('/^audit185_[0-9a-f]{20}$/D', $database) === 1, 'not a probe-owned database');
    foreach ([
        'APP_ENV'=>'testing', 'APP_DEBUG'=>'false', 'APP_KEY'=>'base64:'.base64_encode(str_repeat('a',32)),
        'DB_CONNECTION'=>'mysql', 'DB_HOST'=>'127.0.0.1', 'DB_PORT'=>'3306', 'DB_DATABASE'=>$database,
        'DB_USERNAME'=>'root', 'DB_PASSWORD'=>'audit-isolated-fixture-only', 'CACHE_STORE'=>'array',
        'SESSION_DRIVER'=>'array', 'QUEUE_CONNECTION'=>'sync', 'MAIL_MAILER'=>'array', 'BCRYPT_ROUNDS'=>'4',
    ] as $k=>$v) { putenv($k.'='.$v); $_ENV[$k]=$v; $_SERVER[$k]=$v; }
    require $root.'/vendor/autoload.php';
    $app = require $root.'/bootstrap/app.php';
    $app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
    check(config('database.connections.mysql.host') === '127.0.0.1', 'non-local database refused');
    check(config('database.connections.mysql.database') === $database, 'wrong database refused');
    Illuminate\Support\Facades\DB::statement('SET SESSION innodb_lock_wait_timeout = 5');
    return $app;
}
function executeReset(object $app, string $email, string $token, string $password): string {
    return $app->make(App\Identity\Credentials\PasswordResetCompleter::class)->complete([
        'email'=>$email,'token'=>$token,'password'=>$password,'password_confirmation'=>$password,
    ]);
}

check(getenv('OTERYN_AUDIT185_ISOLATED_DB') === '1', 'explicit isolated-database consent required');
$mode = $argv[1] ?? '';
check(in_array($mode, ['parent','worker'], true), 'mode must be parent or worker');
$root = realpath($argv[2] ?? '');
check($root !== false && is_file($root.'/vendor/autoload.php'), 'provider checkout/dependencies missing');
check(command(['git','rev-parse','HEAD'], $root) === SOURCE_SHA, 'wrong provider source');
check(command(['git','rev-parse','HEAD^{tree}'], $root) === SOURCE_TREE, 'wrong provider tree');
check(command(['git','status','--porcelain','--untracked-files=no'], $root) === '', 'dirty provider source refused');

if ($mode === 'worker') {
    $job = json_decode(file_get_contents($argv[3]), true, 512, JSON_THROW_ON_ERROR);
    $index = (int)($argv[4] ?? -1); check(in_array($index,[0,1],true), 'invalid worker');
    $app = boot($root, $job['database']); $waited = false;
    // Observation barrier after the real token SELECT, not a substituted repository or broker.
    Illuminate\Support\Facades\DB::listen(function ($query) use (&$waited,$job,$index): void {
        if (!$waited && preg_match('/^select\s/i', $query->sql) && str_contains($query->sql,'password_reset_tokens')) {
            $waited=true; file_put_contents($job['barrier'].'/'.$index, 'ready');
            $deadline=microtime(true)+8;
            while (!is_file($job['barrier'].'/'.(1-$index))) {
                check(microtime(true)<$deadline,'token-read barrier timeout'); usleep(10000);
            }
        }
    });
    try {
        $status=executeReset($app,$job['email'],$job['token'],'Audit-Only-Correct-'.$index.'!Password');
        $result=['status'=>$status,'token_read_barrier_reached'=>$waited];
    } catch (Throwable $e) {
        $result=['exception_class'=>get_class($e),'exception_code'=>(string)$e->getCode(),'token_read_barrier_reached'=>$waited];
    }
    file_put_contents($job['barrier'].'/result-'.$index.'.json',json_encode($result,JSON_THROW_ON_ERROR));
    exit(0);
}

$out=$argv[3]??'';check($out!==''&&!file_exists($out),'output must be a new directory');
check(mkdir($out,0700,true),'cannot create output');$out=realpath($out);
$database='audit185_'.bin2hex(random_bytes(10));
$admin=new PDO('mysql:host=127.0.0.1;port=3306;charset=utf8mb4','root','audit-isolated-fixture-only',[
    PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION,PDO::ATTR_TIMEOUT=>5,
]);
$children=[];$report=['source_sha'=>SOURCE_SHA,'source_tree'=>SOURCE_TREE,'scope'=>'Isolated real MariaDB; real PasswordResetCompleter; synthetic identity; no HTTP or production qualification','trials'=>[]];
try {
    $admin->exec('CREATE DATABASE `'.$database.'` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci');
    $app=boot($root,$database);
    $kernel=$app->make(Illuminate\Contracts\Console\Kernel::class);
    check($kernel->call('migrate',['--force'=>true])===0,'isolated migrations failed');
    file_put_contents($out.'/migrations.log',$kernel->output());
    $report['database_version']=$admin->query('SELECT VERSION()')->fetchColumn();
    $report['isolation']=$admin->query('SELECT @@tx_isolation')->fetchColumn();
    $report['source_blobs']=[];
    foreach (['app/Identity/Credentials/PasswordResetCompleter.php','app/Identity/Credentials/IdentityCredentialUpdater.php',
              'vendor/laravel/framework/src/Illuminate/Auth/Passwords/PasswordBroker.php',
              'vendor/laravel/framework/src/Illuminate/Auth/Passwords/DatabaseTokenRepository.php'] as $path) {
        $raw=file_get_contents($root.'/'.$path);
        $report['source_blobs'][$path]=['git_blob'=>sha1('blob '.strlen($raw)."\0".$raw),'sha256'=>hash('sha256',$raw)];
    }
    for($trial=0;$trial<3;$trial++) {
        $identity=App\Identity\Models\Identity::query()->create([
            'email'=>'audit-reset-'.$trial.'@example.invalid','password'=>Illuminate\Support\Facades\Hash::make('Audit-Only-Initial!Password'),
        ]);
        $token=Illuminate\Support\Facades\Password::broker('identities')->createToken($identity);
        if($trial===0) {
            $bad=executeReset($app,$identity->email,'incorrect-token','Audit-Only-Control!Password');
            $first=executeReset($app,$identity->email,$token,'Audit-Only-Control!Password');
            $replay=executeReset($app,$identity->email,$token,'Audit-Only-Replay!Password');
            check($bad===Illuminate\Support\Facades\Password::INVALID_TOKEN,'invalid token control failed');
            check($first===Illuminate\Support\Facades\Password::PASSWORD_RESET,'valid token control failed');
            check($replay===Illuminate\Support\Facades\Password::INVALID_TOKEN,'serial replay control failed');
            $report['controls']=['invalid'=>$bad,'first'=>$first,'serial_replay'=>$replay];
            continue;
        }
        $barrier=$out.'/trial-'.$trial;check(mkdir($barrier,0700),'barrier create failed');
        $job=$barrier.'/job.json';file_put_contents($job,json_encode(['database'=>$database,'email'=>$identity->email,'token'=>$token,'barrier'=>$barrier],JSON_THROW_ON_ERROR));chmod($job,0600);
        for($i=0;$i<2;$i++) {
            $p=proc_open([PHP_BINARY,__FILE__,'worker',$root,$job,(string)$i],[0=>['file','/dev/null','r'],1=>['file',$barrier.'/worker-'.$i.'.log','w'],2=>['file',$barrier.'/worker-'.$i.'.log','a']],$pipes,$root);
            check(is_resource($p),'worker start failed');$children[]=$p;
        }
        $deadline=microtime(true)+25;$statuses=[];
        do {
            $running=false;
            foreach($children as $i=>$p) { $s=proc_get_status($p); if($s['running']){$running=true;} elseif(!isset($statuses[$i])){$statuses[$i]=$s['exitcode'];} }
            check(microtime(true)<$deadline,'worker deadline exceeded');
            if($running){usleep(20000);}
        } while($running);
        foreach($children as $p){proc_close($p);} $children=[];
        unlink($job); // Never retain synthetic one-time token in published evidence.
        $results=[];
        for($i=0;$i<2;$i++) {check(($statuses[$i]??-1)===0,'worker failed');$results[]=json_decode(file_get_contents($barrier.'/result-'.$i.'.json'),true,512,JSON_THROW_ON_ERROR);}
        $fresh=App\Identity\Models\Identity::query()->findOrFail($identity->id);
        $report['trials'][]=['worker_results'=>$results,'successful_resets'=>count(array_filter($results,fn($x)=>($x['status']??null)===Illuminate\Support\Facades\Password::PASSWORD_RESET)),
            'web_generation'=>$fresh->web_session_generation,'game_generation'=>$fresh->game_auth_generation,
            'token_rows_remaining'=>Illuminate\Support\Facades\DB::table('password_reset_tokens')->where('email',$identity->email)->count()];
    }
    $report['hypothesis_reproduced']=count(array_filter($report['trials'],fn($t)=>$t['successful_resets']===2))>0;
} finally {
    foreach($children as $p){proc_terminate($p,9);proc_close($p);}
    foreach(glob($out.'/trial-*/job.json')?:[] as $p){unlink($p);}
    $admin->exec('DROP DATABASE IF EXISTS `'.$database.'`');
}
file_put_contents($out.'/result.json',json_encode($report,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR)."\n");
echo json_encode($report,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR),"\n";
