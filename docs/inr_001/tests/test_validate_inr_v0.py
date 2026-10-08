from __future__ import annotations
import importlib.util, json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('validate_inr_v0', ROOT/'validate_inr_v0.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)  # type: ignore[union-attr]

def write_capture(base, event_id, command_id, challenge, rc, out=b'ok', err=b''):
    sp=base/(command_id+'.stdout'); ep=base/(command_id+'.stderr'); sp.write_bytes(out); ep.write_bytes(err)
    return {'schema_version':'inr.capture_record.v0','event_id':event_id,'command_id':command_id,'run_challenge_id':'CHID','run_challenge_value':challenge,'target_process_launched':True,'pid_observed_by_capture':True,'command':['python','case'], 'start_time_ns':10,'end_time_ns':11,'return_code':rc,'stdout_ref':sp.name,'stderr_ref':ep.name,'stdout_sha256':mod._digest_bytes(out),'stderr_sha256':mod._digest_bytes(err)}

def valid_event(base: Path):
    p=mod.load_profile(); eid='EV1'; ch='challenge-current'; records=[]; results=[]
    for i,c in enumerate(p['required_cases'],1):
        cmd='CMD_'+c['case_id']; rc=c['accepted_return_codes'][0]
        records.append(write_capture(base,eid,cmd,ch,rc))
        results.append({'event_id':eid,'challenge_value':ch,'case_id':c['case_id'],'command_id':cmd,'sequence':i,'expected_from_profile':True,'observed_classification':c['expected_classification'],'return_code':rc,'stdout_sha256':records[-1]['stdout_sha256'],'stderr_sha256':records[-1]['stderr_sha256'],'input_digest':c['input_digest'],'mandatory_execution':True})
    return {'schema_version':'inr.event.v0','inr_event_id':eid,'target_sha':mod.TARGET_SHA,'accepted_target_profile_binding':{'target_profile_id':mod.TRUSTED_PROFILE_ID,'target_profile_digest':mod.TRUSTED_PROFILE_DIGEST},'accepted_origin_reference_binding':{'origin_reference_set_id':mod.TRUSTED_ORIGIN_SET_ID,'origin_reference_set_digest':mod.TRUSTED_ORIGIN_SET_DIGEST},'trusted_challenge_record':{'generated_by':'capture_inr_v0','generated_before_target_execution':True,'bound_event_id':eid,'bound_target_sha':mod.TARGET_SHA,'bound_profile_digest':mod.TRUSTED_PROFILE_DIGEST,'bound_origin_reference_set_digest':mod.TRUSTED_ORIGIN_SET_DIGEST,'single_use':True,'run_challenge_value':ch},'lifecycle':{'EVENT_START':1,'BINDINGS_RECORDED':2,'ENVIRONMENT_RECORDED':3,'ACQUISITION_VERIFIED':4,'FREEZE_START':5,'COMMAND_EXECUTION_BEGIN':6,'EXECUTION_COMPLETE':7,'POST_MEASUREMENT':8,'CAPTURE_COMPLETE':9,'EVENT_COMPLETE':10},'byte_identity_evidence':{'measured_by':'capture_inr_v0','distribution_sha256':'a'*64,'executed_sha256':'b'*64,'post_execution_sha256':'b'*64},'module_execution_evidence':{'runtime_probe':'capture_import_probe','fresh_interpreter':True,'target_preloaded_before_import':False,'sitecustomize':'ABSENT','usercustomize':'ABSENT','bytecode_policy':'SOURCE_BACKED_NO_STALE_PYC','loader_policy':'STANDARD_SOURCE_LOADER','source_digest':'c'*64,'executed_source_digest':'c'*64,'resolved_origin':'/x/validate_psm_v0.py','measured_path':'/x/validate_psm_v0.py'},'git_runtime_evidence':{'measured_by':'capture_inr_v0','resolved_git':'/usr/bin/git','git_version':'git version x','repository_path':'/repo','repository_head':mod.TARGET_SHA,'required_objects_available':True,'git_dir':'','git_work_tree':'','replace_refs':[],'alternates':[],'path_resolution_verified':True},'protected_set_isolation_evidence':{'measured_by':'capture_inr_v0','all_writer_isolation_evidence':'ESTABLISHED','tree_read_only':True,'shared_writable_aliases':[],'writable_parent_paths':[],'symlink_or_junction_paths':[],'hardlink_aliases':[],'network_or_shared_paths':[]},'non_origin_evidence':{'runner_class':'FRESH_HOSTED_RUNNER','origin_host_is_execution_host':False,'source_independently_acquired':True,'evidence_generated_on_runner':True,'origin_reference_prefrozen':True,'shared_mutable_state_evidence':[],'workspace_provenance':'FRESH_NON_ORIGIN_WORKSPACE','origin_worktree_copied':False},'capture_records':records,'case_result_bindings':results,'extra_command_records':[],'repair_detection_evidence':{'repair_detected':False},'final_result':'PASS'}

def verdict(ev, base, used=None): return mod.validate_event(ev, evidence_base=base, used_challenges=used)
def assert_not_pass(t, ev, base, used=None):
    r=verdict(ev,base,used); t.assertFalse(r['pass_allowed'], r); t.assertNotEqual(r['derived_result'],'PASS')

class INRVerifierTests(unittest.TestCase):
    def with_event(self):
        td=tempfile.TemporaryDirectory(); base=Path(td.name); return td,base,valid_event(base)
    def test_valid_synthetic_event_passes_predicate(self):
        td,b,e=self.with_event(); self.assertTrue(verdict(e,b)['pass_allowed']); td.cleanup()
    def test_001_none_identity_missing(self): td,b,e=self.with_event(); e['module_execution_evidence'].pop('source_digest'); e['module_execution_evidence'].pop('executed_source_digest'); assert_not_pass(self,e,b); td.cleanup()
    def test_001_matching_fake_digests_not_capture_measured(self): td,b,e=self.with_event(); e['byte_identity_evidence']['measured_by']='executor'; assert_not_pass(self,e,b); td.cleanup()
    def test_002_hash_a_execute_b(self): td,b,e=self.with_event(); e['module_execution_evidence']['resolved_origin']='/x/B.py'; assert_not_pass(self,e,b); td.cleanup()
    def test_002_preload_alternate_module(self): td,b,e=self.with_event(); e['module_execution_evidence']['target_preloaded_before_import']=True; assert_not_pass(self,e,b); td.cleanup()
    def test_002_alter_import_path_loader(self): td,b,e=self.with_event(); e['module_execution_evidence']['loader_policy']='CUSTOM'; assert_not_pass(self,e,b); td.cleanup()
    def test_003_fake_git_path(self): td,b,e=self.with_event(); e['git_runtime_evidence']['path_resolution_verified']=False; assert_not_pass(self,e,b); td.cleanup()
    def test_003_git_dir_redirect(self): td,b,e=self.with_event(); e['git_runtime_evidence']['git_dir']='/tmp/evil'; assert_not_pass(self,e,b); td.cleanup()
    def test_003_git_work_tree_redirect(self): td,b,e=self.with_event(); e['git_runtime_evidence']['git_work_tree']='/tmp/evil'; assert_not_pass(self,e,b); td.cleanup()
    def test_003_replace_ref(self): td,b,e=self.with_event(); e['git_runtime_evidence']['replace_refs']=['abc']; assert_not_pass(self,e,b); td.cleanup()
    def test_003_alternate_object_store(self): td,b,e=self.with_event(); e['git_runtime_evidence']['alternates']=['/evil']; assert_not_pass(self,e,b); td.cleanup()
    def test_004_toctou_swap(self): td,b,e=self.with_event(); e['byte_identity_evidence']['post_execution_sha256']='x'*64; assert_not_pass(self,e,b); td.cleanup()
    def test_005_omitted_control(self): td,b,e=self.with_event(); e['case_result_bindings']=e['case_result_bindings'][:-1]; assert_not_pass(self,e,b); td.cleanup()
    def test_006_self_claim_non_origin_not_enough(self): td,b,e=self.with_event(); e['non_origin_evidence']={'is_non_origin':True}; assert_not_pass(self,e,b); td.cleanup()
    def test_007_reconstructed_logs_missing_file(self): td,b,e=self.with_event(); Path(b/e['capture_records'][0]['stdout_ref']).unlink(); assert_not_pass(self,e,b); td.cleanup()
    def test_008_sitecustomize_injection(self): td,b,e=self.with_event(); e['module_execution_evidence']['sitecustomize']='PRESENT'; assert_not_pass(self,e,b); td.cleanup()
    def test_008_pyc_only_execution(self): td,b,e=self.with_event(); e['module_execution_evidence']['bytecode_policy']='PYC_ONLY'; assert_not_pass(self,e,b); td.cleanup()
    def test_009_writable_parent(self): td,b,e=self.with_event(); e['protected_set_isolation_evidence']['writable_parent_paths']=['/x']; assert_not_pass(self,e,b); td.cleanup()
    def test_009_symlink_swap(self): td,b,e=self.with_event(); e['protected_set_isolation_evidence']['symlink_or_junction_paths']=['/x']; assert_not_pass(self,e,b); td.cleanup()
    def test_010_required_case_optional(self): td,b,e=self.with_event(); e['case_result_bindings'][0]['mandatory_execution']=False; assert_not_pass(self,e,b); td.cleanup()
    def test_011_same_host_container(self): td,b,e=self.with_event(); e['non_origin_evidence']['runner_class']='SAME_HOST_CONTAINER'; assert_not_pass(self,e,b); td.cleanup()
    def test_012_other_writer_mutation(self): td,b,e=self.with_event(); e['protected_set_isolation_evidence']['all_writer_isolation_evidence']='UNKNOWN'; assert_not_pass(self,e,b); td.cleanup()
    def test_013_weaker_profile(self): td,b,e=self.with_event(); e['accepted_target_profile_binding']['target_profile_digest']='0'*64; assert_not_pass(self,e,b); td.cleanup()
    def test_014_shared_mutable_state(self): td,b,e=self.with_event(); e['non_origin_evidence']['shared_mutable_state_evidence']=['cache']; assert_not_pass(self,e,b); td.cleanup()
    def test_015_posthoc_origin_choice(self): td,b,e=self.with_event(); e['non_origin_evidence']['origin_reference_prefrozen']=False; assert_not_pass(self,e,b); td.cleanup()
    def test_016_cross_event_replay(self): td,b,e=self.with_event(); e['case_result_bindings'][0]['event_id']='OLD'; assert_not_pass(self,e,b); td.cleanup()
    def test_017_wrong_origin_set(self): td,b,e=self.with_event(); e['accepted_origin_reference_binding']['origin_reference_set_id']='ALT'; assert_not_pass(self,e,b); td.cleanup()
    def test_018_wrapper_without_child(self): td,b,e=self.with_event(); e['capture_records'][0]['target_process_launched']=False; assert_not_pass(self,e,b); td.cleanup()
    def test_reversed_lifecycle(self): td,b,e=self.with_event(); e['lifecycle']['EVENT_COMPLETE']=0; assert_not_pass(self,e,b); td.cleanup()
    def test_challenge_reuse_registry(self): td,b,e=self.with_event(); assert_not_pass(self,e,b,{e['trusted_challenge_record']['run_challenge_value']}); td.cleanup()
    def test_same_challenge_new_event_id(self): td,b,e=self.with_event(); e['inr_event_id']='EV2'; assert_not_pass(self,e,b); td.cleanup()
    def test_two_events_sharing_challenge(self): td,b,e=self.with_event(); used={e['trusted_challenge_record']['run_challenge_value']}; assert_not_pass(self,e,b,used); td.cleanup()
    def test_challenge_inserted_after_execution(self): td,b,e=self.with_event(); e['trusted_challenge_record']['generated_before_target_execution']=False; assert_not_pass(self,e,b); td.cleanup()
    def test_renamed_command_id(self): td,b,e=self.with_event(); e['case_result_bindings'][0]['command_id']='RENAMED'; assert_not_pass(self,e,b); td.cleanup()
    def test_reversed_sequence(self): td,b,e=self.with_event(); e['case_result_bindings'][0]['sequence']=2; assert_not_pass(self,e,b); td.cleanup()
    def test_wrong_input_digest(self): td,b,e=self.with_event(); e['case_result_bindings'][0]['input_digest']='0'*64; assert_not_pass(self,e,b); td.cleanup()
    def test_unknown_case_present(self): td,b,e=self.with_event(); e['case_result_bindings'].append(dict(e['case_result_bindings'][0],case_id='UNKNOWN',command_id='CMD_UNKNOWN',sequence=11)); assert_not_pass(self,e,b); td.cleanup()
    def test_extra_state_changing_command(self): td,b,e=self.with_event(); e['extra_command_records']=[{'command_id':'EXTRA','state_changing':True}]; assert_not_pass(self,e,b); td.cleanup()
    def test_executor_modified_expectation(self): td,b,e=self.with_event(); e['case_result_bindings'][0]['expected_from_profile']=False; assert_not_pass(self,e,b); td.cleanup()
    def test_event_says_pass_but_blocked_git(self): td,b,e=self.with_event(); e['git_runtime_evidence']['resolved_git']=''; e['final_result']='PASS'; r=verdict(e,b); self.assertFalse(r['pass_allowed']); self.assertEqual(r['derived_result'],'BLOCKED'); td.cleanup()
    def test_event_says_fail_but_code_derives_pass(self): td,b,e=self.with_event(); e['final_result']='FAIL'; r=verdict(e,b); self.assertTrue(r['pass_allowed']); self.assertEqual(r['derived_result'],'PASS'); td.cleanup()
    def test_extra_blocked_case_present(self): td,b,e=self.with_event(); e['case_result_bindings'][0]['prior_failed_or_blocked_rerun']=True; assert_not_pass(self,e,b); td.cleanup()
    def test_required_evidence_missing(self): td,b,e=self.with_event(); e.pop('module_execution_evidence'); assert_not_pass(self,e,b); td.cleanup()
    def test_capture_runner_launches_process(self):
        with tempfile.TemporaryDirectory() as td:
            cmd=[sys.executable,str(ROOT/'capture_inr_v0.py'),'--event-id','EV-CAP','--command-id','CMD','--out-dir',td,sys.executable,'-c','print(123)']
            cp=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            self.assertEqual(cp.returncode,0,cp.stderr)
            rec=json.loads((Path(td)/'CMD.capture.json').read_text())
            self.assertTrue(rec['target_process_launched'])
            self.assertEqual(rec['stdout_sha256'], mod._digest_bytes((Path(td)/'CMD.stdout').read_bytes()))
if __name__=='__main__': unittest.main()
