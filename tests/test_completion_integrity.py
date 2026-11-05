"""Historical completion regressions: dropped requirements and invented evidence.

Uses actual anchored contracts, signed ledger and evaluator; no service mocks.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError
from typer.testing import CliRunner
from agentwitness.cli import app
from agentwitness.contracts.models import Requirement, RequirementType, TaskContract, TaskStatus
from agentwitness.contracts.storage import ContractStorage
from agentwitness.contracts.evaluator import ContractEvaluator
from agentwitness.crypto import CryptoSigner
from agentwitness.ledger import Ledger
from agentwitness.models import ExecutionStatus, PolicyDecision, Receipt, RemoteGitEvidence


class CompletionIntegrityRegression(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.ledger = Ledger(root / 'receipts.jsonl', CryptoSigner(root / 'keys'))
        self.storage = ContractStorage(root / 'tasks', self.ledger)

    def contract(self, requirements, **kwargs):
        return TaskContract(task_id='historical', session_id='original', title='Preserve original acceptance',
                            created_at='2026-11-06', requirements=requirements, **kwargs)

    def test_no_mandatory_criteria_cannot_produce_done(self):
        # An empty generated acceptance list silently drops every original requirement.
        for requirements in ([], [Requirement(type=RequirementType.TESTS_PASS, required=False)]):
            with self.subTest(requirements=requirements):
                contract = self.contract(requirements, contract_version=1)
                result = ContractEvaluator(self.ledger).evaluate(contract)
                self.assertEqual(result.status, TaskStatus.BLOCKED)
                self.assertIn('mandatory', result.results[0].explanation)

    def test_unrecognised_original_exclusion_cannot_silently_disappear(self):
        # PR #458 motivated this: technical tests passed despite an exclusion breach.
        # AgentWitness lacks semantic correspondence checks, so reject an unsupported
        # exclusion field instead of pretending it was stored/enforced.
        with self.assertRaises(ValidationError):
            self.contract([Requirement(type=RequirementType.TESTS_PASS)],
                          exclusions=['No Council correspondence deliverable'])

    def test_unrecognised_requirement_cannot_silently_disappear(self):
        with self.assertRaises(ValidationError):
            Requirement(type=RequirementType.TESTS_PASS, exclusion='No correspondence')

    def test_cli_rejects_unsupported_exclusion_and_empty_acceptance(self):
        path = Path(self.temp.name) / 'contract.yaml'
        for suffix in ('exclusions: [No correspondence]\nrequirements: [{type: tests_pass}]\n',
                       'requirements: []\n',
                       'requirements: [{type: tests_pass, exclusion: No correspondence}]\n'):
            with self.subTest(suffix=suffix):
                path.write_text('task_id: original\n' + suffix)
                with patch('agentwitness.cli.ContractStorage') as storage:
                    result = CliRunner().invoke(app, ['task', 'create', str(path)])
                    self.assertNotEqual(result.exit_code, 0)
                    storage.assert_not_called()

    def test_valid_signed_evidence_accepted_then_forged_receipt_rejected(self):
        req = Requirement(type=RequirementType.REMOTE_SHA_MATCH,
                          parameters={'commit_sha': 'tested-revision'})
        contract = self.contract([req])
        self.storage.save(contract)
        self.ledger.append(Receipt(receipt_id='observed', session_id='original',
            timestamp_start='t', timestamp_end='t', cwd='/', resolved_executable='git',
            argv=['push'], policy_decision=PolicyDecision.ALLOW,
            execution_status=ExecutionStatus.SUCCEEDED,
            environmental_evidence=[RemoteGitEvidence(local_head='tested-revision',
                remote_head='tested-revision', remote_verified=True)]))
        self.assertEqual(ContractEvaluator(self.ledger).evaluate(contract).status, TaskStatus.DONE)
        rows = self.ledger.filepath.read_text().splitlines()
        forged = json.loads(rows[-1])
        forged['environmental_evidence'][0]['remote_head'] = 'invented-revision'
        rows[-1] = json.dumps(forged)
        self.ledger.filepath.write_text('\n'.join(rows) + '\n')
        self.assertEqual(ContractEvaluator(self.ledger).evaluate(contract).status, TaskStatus.BLOCKED)

    def test_interrupted_contract_load_preserves_unfinished_requirement(self):
        contract = self.contract([Requirement(type=RequirementType.TESTS_PASS)])
        self.storage.save(contract)
        resumed = ContractStorage(self.storage.directory, self.ledger).load(contract.task_id)
        self.assertEqual(resumed.canonical_hash(), contract.canonical_hash())
        self.assertEqual(ContractEvaluator(self.ledger).evaluate(resumed).status,
                         TaskStatus.READY_FOR_VERIFICATION)


if __name__ == '__main__':
    unittest.main()
