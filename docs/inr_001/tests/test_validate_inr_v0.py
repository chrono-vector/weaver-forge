from __future__ import annotations
import importlib.util, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validate_inr_v0', ROOT / 'validate_inr_v0.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)  # type: ignore[union-attr]

def valid_event():
    p = mod.load_profile(); ch='challenge-current'
    results=[]
    for i,c in enumerate(p['required_cases'],1):
        results.append({'event_id':'EV1','challenge_value':ch,'case_id':c['case_id'],'command_id':'CMD_'+c['case_id'],'sequence':i,'expected_from_profile':True,'observed_classification':c['expected_classification'],'return_code':c['accepted_return_codes'][0],'mandatory_execution':True})
    return {
        'schema_version':'inr.event.v0','inr_event_id':'EV1','target_sha':mod.TARGET_SHA,
        'accepted_target_profile_binding':{'target_profile_id':mod.TRUSTED_PROFILE_ID,'target_profile_digest':mod.TRUSTED_PROFILE_DIGEST},
        'accepted_origin_reference_binding':{'origin_reference_set_id':mod.TRUSTED_ORIGIN_SET_ID,'origin_reference_set_digest':mod.TRUSTED_ORIGIN_SET_DIGEST},
        'run_challenge':{'run_challenge_id':'CH1','run_challenge_value':ch,'single_use':True,'bound_event_id':'EV1','reuse_status':'UNUSED'},
        'lifecycle':{'EVENT_START':'t1','FREEZE_START':'t2','CAPTURE_COMPLETE':'t3','EVENT_COMPLETE':'t4'},
        'byte_identity':{'distribution_sha256':'a'*64,'executed_sha256':'b'*64,'executed_bytes_bound':True,'post_execution_sha256':'b'*64},
        'module_execution':{'fresh_interpreter':True,'target_preloaded':False,'sitecustomize':'ABSENT','usercustomize':'ABSENT','bytecode_policy':'SOURCE_BACKED_NO_STALE_PYC','loader_policy':'STANDARD_SOURCE_LOADER','source_digest':'c'*64,'executed_source_digest':'c'*64,'resolved_origin':'/x/validate_psm_v0.py','measured_path':'/x/validate_psm_v0.py'},
        'git_runtime':{'resolved_git':'/usr/bin/git','git_version':'git version x','repository_head':mod.TARGET_SHA,'git_dir_redirect':False,'git_work_tree_redirect':False,'replace_refs':[],'wrapper_risk':False},
        'protected_set_isolation':{'all_writer_isolation':True,'tree_read_only':True,'shared_writable_aliases':[],'writable_parent_risk':False,'symlink_or_junction_risk':False,'hardlink_alias_risk':False},
        'non_origin':{'runner_class':'FRESH_HOSTED_RUNNER','origin_host_is_execution_host':False,'shared_mutable_state':[],'source_independently_acquired':True,'evidence_generated_on_runner':True,'origin_reference_prefrozen':True},
        'capture_provenance':{'capture_launched_target':True,'direct_stdout_stderr':True,'exit_status_from_child':True,'historical_output_only':False,'event_id':'EV1','challenge_value':ch},
        'case_result_bindings':results,'extra_command_records':[], 'repair_detection':{'repair_detected':False},'final_result':'PASS'}

def assert_not_pass(test, ev):
    r=mod.validate_event(ev); test.assertFalse(r['pass_allowed'], r); test.assertNotEqual(r['derived_result'],'PASS')

class INRVerifierTests(unittest.TestCase):
    def test_valid_synthetic_event_passes_predicate(self): self.assertTrue(mod.validate_event(valid_event())['pass_allowed'])
    def test_mf001_executed_byte_mismatch(self): ev=valid_event(); ev['byte_identity']['post_execution_sha256']='x'*64; assert_not_pass(self, ev)
    def test_mf002_hash_a_execute_b(self): ev=valid_event(); ev['module_execution']['executed_source_digest']='d'*64; assert_not_pass(self, ev)
    def test_mf003_fake_git_runtime(self): ev=valid_event(); ev['git_runtime']['wrapper_risk']=True; assert_not_pass(self, ev)
    def test_mf004_toctou_swap(self): ev=valid_event(); ev['protected_set_isolation']['tree_read_only']=False; assert_not_pass(self, ev)
    def test_mf005_omitted_control(self): ev=valid_event(); ev['case_result_bindings']=ev['case_result_bindings'][:-1]; assert_not_pass(self, ev)
    def test_mf006_fake_non_origin(self): ev=valid_event(); ev['non_origin']['source_independently_acquired']=False; assert_not_pass(self, ev)
    def test_mf007_reconstructed_logs(self): ev=valid_event(); ev['capture_provenance']['historical_output_only']=True; assert_not_pass(self, ev)
    def test_mf008_preload_or_loader(self): ev=valid_event(); ev['module_execution']['target_preloaded']=True; assert_not_pass(self, ev)
    def test_mf009_writable_parent_or_symlink(self): ev=valid_event(); ev['protected_set_isolation']['writable_parent_risk']=True; assert_not_pass(self, ev)
    def test_mf010_weakened_profile(self): ev=valid_event(); ev['case_result_bindings'][1]['mandatory_execution']=False; assert_not_pass(self, ev)
    def test_mf011_same_host_container(self): ev=valid_event(); ev['non_origin']['runner_class']='SAME_HOST_CONTAINER'; assert_not_pass(self, ev)
    def test_mf012_other_writer_mutation(self): ev=valid_event(); ev['protected_set_isolation']['all_writer_isolation']=False; assert_not_pass(self, ev)
    def test_mf013_wrong_target_profile(self): ev=valid_event(); ev['accepted_target_profile_binding']['target_profile_digest']='0'*64; assert_not_pass(self, ev)
    def test_mf014_shared_mutable_state(self): ev=valid_event(); ev['non_origin']['shared_mutable_state']=['origin-cache']; assert_not_pass(self, ev)
    def test_mf015_posthoc_origin_reference(self): ev=valid_event(); ev['non_origin']['origin_reference_prefrozen']=False; assert_not_pass(self, ev)
    def test_mf016_cross_event_replay(self): ev=valid_event(); ev['case_result_bindings'][0]['event_id']='OLD'; assert_not_pass(self, ev)
    def test_mf017_wrong_origin_set(self): ev=valid_event(); ev['accepted_origin_reference_binding']['origin_reference_set_id']='ALT'; assert_not_pass(self, ev)
    def test_mf018_wrapper_without_child(self): ev=valid_event(); ev['capture_provenance']['capture_launched_target']=False; assert_not_pass(self, ev)
    def test_capture_runner_launches_process(self):
        with tempfile.TemporaryDirectory() as td:
            cmd=[sys.executable, str(ROOT/'capture_inr_v0.py'), '--event-id','EV-CAP','--command-id','CMD','--out-dir',td, sys.executable, '-c', 'print(123)']
            cp=subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(cp.returncode,0,cp.stderr)
            self.assertTrue((Path(td)/'CMD.capture.json').exists())

if __name__ == '__main__': unittest.main()
