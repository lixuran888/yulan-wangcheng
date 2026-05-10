from django.test import SimpleTestCase

from .simulation_core import NETWORK_SCENARIOS, SimulationEngine


class SimulationEngineTests(SimpleTestCase):
    def test_all_networks_can_step(self):
        for network_type in NETWORK_SCENARIOS:
            engine = SimulationEngine(network_type, seed=42)
            before = engine.snapshot()
            after = engine.step()
            self.assertEqual(before["networkType"], network_type)
            self.assertEqual(after["timeStep"], 1)
            self.assertGreater(len(after["nodes"]), 0)
            self.assertIn("report", after)

    def test_intervention_targets_key_nodes(self):
        engine = SimulationEngine("scale_free", seed=42)
        key_nodes = engine.snapshot()["report"]["keyNodes"][:3]
        after = engine.step({"target_nodes": key_nodes, "credibility": 0.9})
        states = {node["id"]: node["currentState"] for node in after["nodes"]}
        self.assertTrue(any(states[node_id] == "DEBUNKING" for node_id in key_nodes))
