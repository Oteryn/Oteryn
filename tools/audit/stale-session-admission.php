<?php
/** Deterministic interleaving of real authentication/revocation/admission components. */
declare(strict_types=1);
if (getenv('OTERYN_AUDIT185_ISOLATED_SESSION') !== '1') { throw new RuntimeException('explicit isolated-session consent required'); }
$root=realpath($argv[1]??'');$output=$argv[2]??'';
if (!$root || $output==='' || file_exists($output)) { throw new RuntimeException('valid checkout and new output required'); }
foreach ([['rev-parse','HEAD','de917b3477a1de0667531380de3660e8b2ab59aa'],['rev-parse','HEAD^{tree}','ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e'],['status','--porcelain','--untracked-files=no','']] as $spec) {
    $expected=array_pop($spec);$process=proc_open(array_merge(['git'],$spec),[0=>['file','/dev/null','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes,$root);
    if(!is_resource($process)){throw new RuntimeException('Git identity process unavailable');}
    $actual=trim(stream_get_contents($pipes[1]));fclose($pipes[1]);fclose($pipes[2]);
    if(proc_close($process)!==0||$actual!==$expected){throw new RuntimeException('wrong or dirty provider source');}
}
foreach (['APP_ENV'=>'testing','APP_DEBUG'=>'false','APP_KEY'=>'base64:'.base64_encode(str_repeat('b',32)),
          'DB_CONNECTION'=>'sqlite','DB_DATABASE'=>':memory:','CACHE_STORE'=>'array','SESSION_DRIVER'=>'array',
          'QUEUE_CONNECTION'=>'sync','MAIL_MAILER'=>'array'] as $k=>$v) {putenv($k.'='.$v);$_ENV[$k]=$v;$_SERVER[$k]=$v;}
require $root.'/vendor/autoload.php';$app=require $root.'/bootstrap/app.php';
$kernel=$app->make(Illuminate\Contracts\Console\Kernel::class);$kernel->bootstrap();
if(config('database.default')!=='sqlite'||config('database.connections.sqlite.database')!==':memory:') {throw new RuntimeException('only in-memory SQLite is allowed');}
if($kernel->call('migrate',['--force'=>true])!==0) {throw new RuntimeException('in-memory migrations failed');}

function requestFor(object $app,string $email,string $password): App\Http\Requests\Identity\LoginIdentityRequest {
    $input=['email'=>$email,'password'=>$password];
    $request=App\Http\Requests\Identity\LoginIdentityRequest::create('/login','POST',$input);
    $request->setContainer($app);$request->setRedirector($app['redirect']);
    $validator=Illuminate\Support\Facades\Validator::make($input,$request->rules());
    if(!$validator->passes()){throw new RuntimeException('synthetic login input rejected');}
    $request->setValidator($validator);
    $session=$app['session']->driver();$session->start();$session->flush();$request->setLaravelSession($session);
    $app->instance('request',$request);$app['auth']->forgetGuards();
    $request->setUserResolver(fn()=>Illuminate\Support\Facades\Auth::user());
    $route=new Illuminate\Routing\Route(['GET'],'/audit-protected',['uses'=>fn()=>new Symfony\Component\HttpFoundation\Response('test',200)]);
    $route->middleware('auth');$request->setRouteResolver(fn()=>$route);
    return $request;
}
$rows=[];
foreach(['positive_current_credentials','negative_existing_session_revoked','stale_credentials_before_revocation_admitted_after']as$case){
    $identity=App\Identity\Models\Identity::query()->create(['email'=>$case.'@example.invalid','password'=>Illuminate\Support\Facades\Hash::make('Audit-Only-Old!Password')]);
    $request=requestFor($app,$identity->email,'Audit-Only-Old!Password');
    $authenticated=$request->authenticate(); // actual password and disabled-state verification
    $authenticatedGeneration=$authenticated->web_session_generation;
    $manager=$app->make(App\Identity\Sessions\IdentityWebSessionManager::class);
    if($case==='stale_credentials_before_revocation_admitted_after'){
        $app->make(App\Identity\Credentials\IdentityCredentialUpdater::class)->reset($identity->fresh(),'Audit-Only-New!Password');
    }
    $manager->login($authenticated);$manager->establish($request,$authenticated);
    if($case==='negative_existing_session_revoked'){
        $app->make(App\Identity\Credentials\IdentityCredentialUpdater::class)->reset($identity->fresh(),'Audit-Only-New!Password');
    }
    $callback=false;
    $response=$app->make(App\Http\Middleware\EnsureIdentitySessionIsCurrent::class)->handle($request,function($request)use(&$callback){$callback=true;return new Symfony\Component\HttpFoundation\Response('protected-control',200);});
    $fresh=$identity->fresh();
    $rows[]=['case'=>$case,'verified_credential_generation'=>$authenticatedGeneration,
             'persisted_generation'=>$fresh->web_session_generation,'session_generation'=>$request->session()->get(App\Identity\Sessions\WebSessionState::GENERATION_KEY),
             'protected_callback_reached'=>$callback,'response_status'=>$response->getStatusCode(),'authenticated_after_gate'=>Illuminate\Support\Facades\Auth::check(),
             'old_password_still_matches'=>Illuminate\Support\Facades\Hash::check('Audit-Only-Old!Password',$fresh->password)];
    $manager->invalidate($request);
}
if(!$rows[0]['protected_callback_reached']||!$rows[0]['authenticated_after_gate']){throw new RuntimeException('positive admission control failed');}
if($rows[1]['protected_callback_reached']||$rows[1]['authenticated_after_gate']||$rows[1]['response_status']!==302){throw new RuntimeException('negative revocation control failed');}
$result=['source_sha'=>'de917b3477a1de0667531380de3660e8b2ab59aa','scope'=>'Real service composition with deterministic revocation interleaving; in-memory synthetic database; not a live HTTP concurrency or production test',
         'controls'=>$rows,'stale_generation_promoted'=>$rows[2]['protected_callback_reached']&&$rows[2]['authenticated_after_gate']&&!$rows[2]['old_password_still_matches']];
file_put_contents($output,json_encode($result,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR)."\n");echo json_encode($result,JSON_PRETTY_PRINT|JSON_THROW_ON_ERROR),"\n";
