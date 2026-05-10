import json
import random
import statistics
import sys
import datetime
import urllib.error
import urllib.request
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


ORIGINAL_BACKEND = Path(__file__).resolve().parents[3] / "generative_agents-main" / "reverie" / "backend_server"
if ORIGINAL_BACKEND.exists() and str(ORIGINAL_BACKEND) not in sys.path:
    sys.path.insert(0, str(ORIGINAL_BACKEND))

try:
    from persona.memory_structures.associative_memory import AssociativeMemory
    from persona.memory_structures.scratch import Scratch
    from persona.prompt_template.gpt_structure import ChatGPT_single_request
    from utils import (
        DEEPSEEK_API_BASE,
        DEEPSEEK_MODEL_NAME,
        LOCAL_API_BASE,
        LOCAL_API_KEY,
        LOCAL_MODEL_NAME,
        USE_LOCAL_MODEL,
        deepseek_api_key,
    )
except Exception:
    AssociativeMemory = None
    Scratch = None
    ChatGPT_single_request = None
    DEEPSEEK_API_BASE = ""
    DEEPSEEK_MODEL_NAME = ""
    LOCAL_API_BASE = ""
    LOCAL_API_KEY = ""
    LOCAL_MODEL_NAME = ""
    USE_LOCAL_MODEL = False
    deepseek_api_key = ""


BASE_DIR = Path(__file__).resolve().parents[1]
PERSONA_DIR = BASE_DIR / "storage" / "base_the_ville_clean" / "personas"

NETWORK_SCENARIOS = {
    "community_network": {
        "label": "\u793e\u533a\u7f51\u7edc",
        "model": "Community-aware Weighted Complex Threshold Model",
        "scene_name": "\u793e\u533a\u5708\u5c42\u8206\u8bba\u4f20\u64ad",
        "description": "\u8282\u70b9\u4f7f\u7528\u539f\u59cb\u5c0f\u9547 Agent \u7684\u4eba\u8bbe\u3001\u8bb0\u5fc6\u4e0e\u793e\u4f1a\u5173\u7cfb\uff0c\u7f51\u7edc\u6309\u201c\u5bb6\u957f/\u6559\u5e08/\u516c\u5171\u8ba8\u8bba/\u4e13\u5bb6/\u7ebf\u4e0a\u9752\u5c11\u5e74\u201d\u7b49\u793e\u533a\u5206\u5c42\u3002\u52a8\u529b\u5b66\u5c42\u91c7\u7528\u793e\u533a\u52a0\u6743\u590d\u6742\u9608\u503c\u6a21\u578b\uff1a\u793e\u533a\u5185\u9ad8\u6743\u91cd\u5f3a\u5316\uff0c\u793e\u533a\u95f4\u9700\u8981\u6865\u63a5\u8282\u70b9\u548c\u8db3\u591f\u5f71\u54cd\u538b\u529b\u624d\u4f1a\u7834\u5708\u4f20\u64ad\u3002",
        "default_trust": 0.58,
        "emotion_amplification": 0.55,
        "alpha_in": 1.0,
        "alpha_out": 0.45,
        "bridge_bonus": 1.3,
    }
}

ACTIVE_STATES = {"EXPOSED", "TALKING", "QUESTIONING", "DEBUNKING", "REFLECTING"}

CONCRETE_EXPERTS = {
    "Education Bureau Representative": {
        "name": "\u8d75\u660e\u8f69",
        "persona": "\u6559\u80b2\u7ba1\u7406\u4e0e\u6821\u56ed\u6cbb\u7406\u76f8\u5173\u4eba\u58eb",
        "innate": "\u8c28\u614e\u3001\u514b\u5236\u3001\u91cd\u89c6\u7a0b\u5e8f\u3001\u5bb3\u6015\u5931\u63a7",
        "learned": "\u8d75\u660e\u8f69\u662f\u533a\u6559\u80b2\u5c40\u5b89\u5168\u529e\u526f\u4e3b\u4efb\uff0c\u5bb6\u91cc\u4e5f\u6709\u4e00\u4e2a\u4e0a\u5c0f\u5b66\u7684\u5973\u513f\u3002\u4ed6\u5e73\u65f6\u8bf4\u8bdd\u5f88\u514b\u5236\uff0c\u559c\u6b22\u5148\u8bb2\u65f6\u95f4\u7ebf\u3001\u6d41\u7a0b\u548c\u8d23\u4efb\u754c\u5b9a\uff0c\u4f46\u9047\u5230\u5bb6\u957f\u60c5\u7eea\u5d29\u6e83\u65f6\u4f1a\u660e\u663e\u7d27\u5f20\u3002\u4ed6\u548c\u6797\u5c0f\u96e8\u6709\u5de5\u4f5c\u8054\u7cfb\uff0c\u5bf9\u674e\u5927\u5f3a\u7684\u6124\u6012\u65e2\u7406\u89e3\u53c8\u62c5\u5fc3\u4e8b\u6001\u5931\u63a7\u3002",
        "currently": "\u8d75\u660e\u8f69\u6b63\u5728\u6838\u5bf9\u5e7c\u513f\u56ed\u4e0a\u62a5\u6750\u6599\u3001\u5bb6\u957f\u6295\u8bc9\u8bb0\u5f55\u548c\u6821\u56ed\u5b89\u5168\u6d41\u7a0b\uff0c\u60f3\u5c3d\u5feb\u7ed9\u51fa\u4e00\u4e2a\u80fd\u8ba9\u5bb6\u957f\u770b\u61c2\u7684\u8bf4\u6cd5\u3002",
    },
    "Market Supervision Expert": {
        "name": "\u9648\u7acb\u8861",
        "persona": "\u98df\u54c1\u5b89\u5168\u4e0e\u5e02\u573a\u76d1\u7ba1\u4eba\u58eb",
        "innate": "\u4e25\u8c28\u3001\u6ce8\u91cd\u7ec6\u8282\u3001\u8bf4\u8bdd\u76f4\u63a5\u3001\u4e0d\u7231\u7a7a\u8bdd",
        "learned": "\u9648\u7acb\u8861\u662f\u5e02\u573a\u76d1\u7ba1\u6240\u98df\u54c1\u5b89\u5168\u68c0\u67e5\u5458\uff0c\u59bb\u5b50\u5728\u836f\u5e97\u5de5\u4f5c\uff0c\u5bb6\u91cc\u7236\u4eb2\u66fe\u7ecf\u5f00\u8fc7\u5c0f\u996d\u9986\u3002\u4ed6\u5bf9\u4f9b\u8d27\u7968\u636e\u3001\u7559\u6837\u8bb0\u5f55\u3001\u51b7\u94fe\u548c\u8fdb\u8d27\u6e20\u9053\u7279\u522b\u654f\u611f\uff0c\u8bf4\u8bdd\u5e38\u5e38\u662f\u201c\u5148\u770b\u5355\u636e\uff0c\u522b\u5148\u4e0b\u7ed3\u8bba\u201d\u3002\u4ed6\u548c\u738b\u4e3d\u534e\u7684\u5496\u5561\u9986\u6709\u68c0\u67e5\u63a5\u89e6\uff0c\u4e5f\u60f3\u627e\u5218\u5c0f\u654f\u6838\u5bf9\u98df\u5802\u73b0\u573a\u7ec6\u8282\u3002",
        "currently": "\u9648\u7acb\u8861\u6b63\u5728\u8ffd\u98df\u5802\u4f9b\u5e94\u5546\u548c\u98df\u6750\u7559\u6837\uff0c\u4ed6\u4e0d\u613f\u610f\u88ab\u60c5\u7eea\u63a8\u7740\u8d70\uff0c\u4f46\u77e5\u9053\u4e00\u65e6\u7968\u636e\u5bf9\u4e0d\u4e0a\uff0c\u4e8b\u60c5\u5c31\u4e0d\u662f\u666e\u901a\u4e8b\u6545\u3002",
    },
    "Public Health Expert": {
        "name": "\u5b59\u5b81",
        "persona": "\u516c\u5171\u536b\u751f\u4e0e\u98ce\u9669\u6c9f\u901a\u4eba\u58eb",
        "innate": "\u6e29\u548c\u3001\u5206\u6790\u578b\u3001\u5171\u60c5\u5f3a\u3001\u4e0d\u8f7b\u6613\u523a\u6fc0\u5bf9\u65b9",
        "learned": "\u5b59\u5b81\u662f\u533a\u75be\u63a7\u4e2d\u5fc3\u516c\u5171\u536b\u751f\u533b\u5e08\uff0c\u6bcd\u4eb2\u662f\u9000\u4f11\u62a4\u58eb\u3002\u5979\u4e60\u60ef\u628a\u5bb6\u957f\u7684\u6050\u614c\u5148\u63a5\u4f4f\uff0c\u518d\u6162\u6162\u89e3\u91ca\u75c7\u72b6\u3001\u6f5c\u4f0f\u671f\u548c\u98ce\u9669\u3002\u5979\u8ba4\u8bc6\u6797\u5c0f\u96e8\uff0c\u4e5f\u4e00\u76f4\u60f3\u8ba9\u5218\u5c0f\u654f\u5728\u5b89\u5168\u7684\u60c5\u51b5\u4e0b\u8bf4\u51fa\u770b\u5230\u7684\u7ec6\u8282\u3002",
        "currently": "\u5b59\u5b81\u6b63\u5728\u6574\u7406\u5b69\u5b50\u75c7\u72b6\u5206\u5e03\u3001\u5c31\u533b\u65f6\u95f4\u548c\u53ef\u7591\u98df\u7269\uff0c\u5979\u6700\u62c5\u5fc3\u7684\u662f\u8c23\u8a00\u5f71\u54cd\u5bb6\u957f\u5c31\u533b\u548c\u540e\u7eed\u8c03\u67e5\u3002",
    },
    "Meeting Moderator": {
        "name": "\u5510\u6653\u8212",
        "persona": "\u793e\u533a\u534f\u8c03\u4e0e\u8bb0\u5f55\u8005",
        "innate": "\u8010\u5fc3\u3001\u5584\u4e8e\u503e\u542c\u3001\u80fd\u63a7\u573a\u3001\u8bb0\u5fc6\u7ec6\u8282",
        "learned": "\u5510\u6653\u8212\u662f\u8857\u9053\u793e\u533a\u5de5\u4f5c\u8005\uff0c\u4e08\u592b\u662f\u51fa\u79df\u8f66\u53f8\u673a\uff0c\u5979\u5e73\u65f6\u8d1f\u8d23\u5bb6\u957f\u6c9f\u901a\u4f1a\u8bae\u548c\u5c45\u6c11\u534f\u8c03\u3002\u5979\u4e0d\u662f\u4e13\u5bb6\uff0c\u4f46\u5f88\u64c5\u957f\u628a\u4e00\u5806\u60c5\u7eea\u5316\u7684\u53d1\u8a00\u6574\u7406\u6210\u95ee\u9898\u6e05\u5355\u3002\u5979\u548c\u738b\u4e3d\u534e\u719f\uff0c\u4e5f\u7ecf\u5e38\u8bf7\u5f20\u56fd\u5e86\u5e2e\u5fd9\u4f20\u8bdd\u3002",
        "currently": "\u5510\u6653\u8212\u5728\u8bb0\u5f55\u5404\u65b9\u8bf4\u6cd5\uff0c\u60f3\u628a\u5bb6\u957f\u7684\u7591\u95ee\u3001\u6559\u5e08\u7684\u56f0\u96be\u548c\u4e13\u5bb6\u7684\u8bc1\u636e\u653e\u5230\u540c\u4e00\u5f20\u8868\u91cc\uff0c\u9632\u6b62\u4f1a\u8bae\u53d8\u6210\u4e92\u76f8\u6307\u8d23\u3002",
    },
}

STATE_LABELS = {
    "UNAWARE": "\u672a\u63a5\u89e6",
    "EXPOSED": "\u5df2\u63a5\u89e6",
    "LISTENING": "\u503e\u542c",
    "TALKING": "\u4ea4\u6d41",
    "QUESTIONING": "\u8d28\u7591",
    "DEBUNKING": "\u8f9f\u8c23",
    "SILENT": "\u6c89\u9ed8",
    "REFLECTING": "\u53cd\u601d",
}


@dataclass
class MemoryNode:
    time_step: int
    kind: str
    content: str
    poignancy: float
    keywords: List[str] = field(default_factory=list)


@dataclass
class AgentMemory:
    associative: List[MemoryNode] = field(default_factory=list)
    reflections: List[MemoryNode] = field(default_factory=list)
    dialogue_history: List[MemoryNode] = field(default_factory=list)
    importance_trigger_curr: float = 0.0
    importance_trigger_max: float = 2.8

    def add(self, time_step: int, kind: str, content: str, poignancy: float, keywords: Optional[List[str]] = None) -> None:
        node = MemoryNode(time_step, kind, content, poignancy, keywords or [])
        self.associative.append(node)
        if kind == "dialogue":
            self.dialogue_history.append(node)
        if kind in {"dialogue", "perceived_dialogue", "intervention"}:
            self.importance_trigger_curr += poignancy
        self.associative = self.associative[-120:]
        self.dialogue_history = self.dialogue_history[-60:]

    def retrieve(self, keywords: Iterable[str], limit: int = 4) -> List[MemoryNode]:
        query = set(keywords)
        ranked = []
        for node in self.associative:
            overlap = len(query.intersection(node.keywords))
            score = overlap * 0.55 + node.poignancy * 0.35 + node.time_step * 0.01
            ranked.append((score, node))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [node for _, node in ranked[:limit]]

    def reflect(self, time_step: int, agent: "Agent", adjacency: Dict[str, Set[str]]) -> Optional[str]:
        if self.importance_trigger_curr < self.importance_trigger_max:
            return None
        evidence_nodes = [
            n for n in self.associative[-18:]
            if n.kind in {"dialogue", "perceived_dialogue", "intervention"}
        ][-4:]
        if len(evidence_nodes) < 2:
            return None
        evidence = "\uff1b".join(n.content[:34] for n in evidence_nodes[-2:])
        degree = len(adjacency.get(agent.id, set()))
        if agent.osi > 0.65:
            content = f"{agent.name}\u7684\u6d1e\u5bdf\uff1a\u4ece\u6700\u8fd1\u7684\u8a00\u8bba\u201c{evidence}\u201d\u770b\uff0c\u6211\u5bf9\u4ed6\u4eba\u610f\u89c1\u8fc7\u4e8e\u654f\u611f\uff0c\u63a5\u4e0b\u6765\u9700\u8981\u5148\u6838\u5bf9\u6765\u6e90\u518d\u7ee7\u7eed\u4f20\u8fbe\u3002"
        elif agent.cpi > 0.58 or degree >= 6:
            content = f"{agent.name}\u7684\u6d1e\u5bdf\uff1a\u6211\u548c{degree}\u4e2a\u719f\u4eba\u76f8\u8fde\uff0c\u6700\u8fd1\u8a00\u8bba\u201c{evidence}\u201d\u4f1a\u88ab\u719f\u4eba\u5173\u7cfb\u653e\u5927\uff0c\u6240\u4ee5\u6211\u8981\u66f4\u8c28\u614e\u5730\u8868\u8fbe\u3002"
        elif agent.trust < 0.42:
            content = f"{agent.name}\u7684\u6d1e\u5bdf\uff1a\u8bc1\u636e\u94fe\u8fd8\u4e0d\u7a33\uff0c\u6211\u8bb0\u4e0b\u4e86\u201c{evidence}\u201d\uff0c\u4f46\u4e0d\u60f3\u628a\u5b83\u5f53\u6210\u5df2\u7ecf\u786e\u8ba4\u7684\u7ed3\u8bba\u3002"
        else:
            content = f"{agent.name}\u7684\u6d1e\u5bdf\uff1a\u6700\u8fd1\u5bf9\u8bdd\u201c{evidence}\u201d\u8ba9\u6211\u5f00\u59cb\u628a\u8ba8\u8bba\u4ece\u60c5\u7eea\u53cd\u5e94\u8f6c\u5230\u8d23\u4efb\u548c\u8bc1\u636e\u4e0a\u3002"
        node = MemoryNode(time_step, "reflection", content, 0.75, ["reflection", "opinion"])
        self.reflections.append(node)
        self.associative.append(node)
        self.importance_trigger_curr = 0.0
        return content


@dataclass
class SocialRelation:
    target_id: str
    relation_type: str
    trust_score: float
    interaction_count: int = 0
    last_message: str = ""


@dataclass
class Agent:
    id: str
    name: str
    persona_type: str
    network_role: str
    community: int
    profile: str
    innate: str
    learned: str
    currently: str
    lifestyle: str
    online_name: str
    state: str = "UNAWARE"
    stance: float = 0.0
    arousal: float = 0.35
    anxiety: float = 0.35
    anger: float = 0.2
    trust: float = 0.55
    osi: float = 0.0
    cpi: float = 0.0
    exposure_count: int = 0
    skepticism: float = 0.35
    social_responsibility: float = 0.45
    activation_pressure: float = 0.0
    activation_threshold: float = 0.55
    memory: AgentMemory = field(default_factory=AgentMemory)
    relations: Dict[str, SocialRelation] = field(default_factory=dict)
    scratch: Any = None
    a_mem: Any = None


def load_original_agents(rng: random.Random) -> Dict[str, Agent]:
    agents = {}
    persona_folders = sorted([p for p in PERSONA_DIR.iterdir() if p.is_dir()], key=lambda p: p.name)
    for idx, folder in enumerate(persona_folders):
        scratch_path = folder / "bootstrap_memory" / "scratch.json"
        if not scratch_path.exists():
            continue
        scratch = json.loads(scratch_path.read_text(encoding="utf-8"))
        aid = f"A{idx:03d}"
        expert_override = CONCRETE_EXPERTS.get(folder.name)
        name = expert_override["name"] if expert_override else (scratch.get("name") or folder.name)
        innate = expert_override["innate"] if expert_override else scratch.get("innate", "")
        learned = expert_override["learned"] if expert_override else scratch.get("learned", "")
        currently = expert_override["currently"] if expert_override else scratch.get("currently", "")
        lifestyle = scratch.get("lifestyle", "")
        online_name = scratch.get("online_name", name)
        friends = scratch.get("friends", {})
        if expert_override:
            persona_type = expert_override["persona"]
        elif friends.get("tensions"):
            persona_type = "\u6709\u5173\u7cfb\u5f20\u529b\u7684\u5c0f\u9547\u5c45\u6c11"
        elif friends.get("best_friends") or friends.get("good_friends"):
            persona_type = "\u719f\u4eba\u5708\u4e2d\u7684\u53c2\u4e0e\u8005"
        else:
            persona_type = "\u89c2\u671b\u578b\u5c0f\u9547\u5c45\u6c11"
        profile = f"{name}\uff0c{innate}\u3002{learned} {currently}".strip()
        agent = Agent(
            id=aid,
            name=name,
            persona_type=persona_type,
            network_role="ordinary_node",
            community=infer_community(folder.name, idx),
            profile=profile,
            innate=innate,
            learned=learned,
            currently=currently,
            lifestyle=lifestyle,
            online_name=online_name,
            stance=rng.uniform(-0.12, 0.12),
            arousal=0.42 if "\u60c5\u7eea" in learned or "\u6124\u6012" in currently else 0.32,
            anxiety=0.45 if "\u62c5\u5fc3" in currently or "\u6050\u60e7" in currently or "\u59d4\u5c48" in currently else 0.32,
            anger=0.42 if "\u6124\u6012" in learned or "\u8fc1\u6012" in currently else 0.20,
            trust=0.55 + rng.uniform(-0.1, 0.1),
            skepticism=infer_skepticism(folder.name, learned, currently),
            social_responsibility=infer_social_responsibility(folder.name, learned, currently),
        )
        attach_original_memory_stream(agent, folder, name, innate, learned, currently)
        agent.memory.add(0, "profile", profile, 0.85, ["profile", name])
        agent.memory.add(0, "current_context", currently or learned, 0.75, ["event", "current"])
        add_bootstrap_memories(agent, folder)
        agents[aid] = agent
    name_to_id = {agent.name: aid for aid, agent in agents.items()}
    attach_original_relations(agents, name_to_id, persona_folders, rng)
    attach_expert_relations(agents)
    return agents


def attach_original_memory_stream(agent: Agent, folder: Path, name: str, innate: str, learned: str, currently: str) -> None:
    if Scratch is None or AssociativeMemory is None:
        return
    try:
        scratch = Scratch(str(folder / "bootstrap_memory" / "scratch.json"))
        scratch.name = name
        scratch.innate = innate
        scratch.learned = learned
        scratch.currently = currently
        scratch.curr_time = datetime.datetime(2026, 5, 11, 9, 0, 0)
        scratch.act_description = "\u53c2\u4e0e\u5c0f\u9547\u5173\u4e8e\u5e7c\u513f\u56ed\u98df\u7269\u4e2d\u6bd2\u4e8b\u4ef6\u7684\u8ba8\u8bba"
        scratch.chat = []
        scratch.chatting_with = None
        scratch.chatting_end_time = None
        agent.scratch = scratch
        agent.a_mem = AssociativeMemory(str(folder / "bootstrap_memory" / "associative_memory"))
    except Exception:
        agent.scratch = None
        agent.a_mem = None


def infer_community(folder_name: str, idx: int) -> int:
    expert_group = {"Education Bureau Representative", "Market Supervision Expert", "Public Health Expert", "Meeting Moderator"}
    parent_group = {"Li Daqiang", "Zhang Guoqing"}
    kindergarten_group = {"Lin Xiaoyu", "Liu Xiaomin"}
    public_discussion_group = {"Wang Lihua", "Chen Siyuan", "Zhou Xiaoyi"}
    online_youth_group = {"Gao Jianguo", "Han Xiaoxue"}
    if folder_name in parent_group:
        return 0
    if folder_name in kindergarten_group:
        return 1
    if folder_name in public_discussion_group:
        return 2
    if folder_name in expert_group:
        return 3
    if folder_name in online_youth_group:
        return 4
    return idx % 5


def infer_skepticism(folder_name: str, learned: str, currently: str) -> float:
    text = f"{folder_name} {learned} {currently}"
    score = 0.34
    if any(k in text for k in ["Expert", "Bureau", "\u6838", "\u76d1\u7763", "\u8c03\u67e5", "\u8bc1\u636e", "\u8d28\u7591"]):
        score += 0.22
    if any(k in text for k in ["\u5b66\u751f", "\u7c89\u4e1d", "\u516b\u5366", "\u60c5\u7eea"]):
        score -= 0.08
    if any(k in text for k in ["\u4e0d\u6562", "\u89c2\u5bdf", "\u6c89\u9ed8", "\u8bb0\u5f55"]):
        score += 0.08
    return clamp(score)


def infer_social_responsibility(folder_name: str, learned: str, currently: str) -> float:
    text = f"{folder_name} {learned} {currently}"
    score = 0.45
    if any(k in text for k in ["Expert", "Bureau", "\u6559\u5e08", "\u5bb6\u957f", "\u5b69\u5b50", "\u516c\u5171", "\u8d23\u4efb"]):
        score += 0.24
    if any(k in text for k in ["\u4e2d\u5fc3", "\u4fe1\u606f", "\u793e\u533a", "\u8bb0\u5f55", "\u91c7\u8bbf"]):
        score += 0.12
    if any(k in text for k in ["\u4e0d\u6562", "\u5bb3\u6015", "\u56de\u907f"]):
        score -= 0.10
    return clamp(score)


def add_bootstrap_memories(agent: Agent, folder: Path) -> None:
    nodes_path = folder / "bootstrap_memory" / "associative_memory" / "nodes.json"
    if not nodes_path.exists():
        return
    try:
        nodes = json.loads(nodes_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    if not isinstance(nodes, dict):
        return
    for node in list(nodes.values())[-20:]:
        desc = node.get("description") or " ".join(str(x) for x in [node.get("subject"), node.get("predicate"), node.get("object")] if x)
        keywords = node.get("keywords") or ["memory"]
        poignancy = float(node.get("poignancy") or 0.45) / 10 if float(node.get("poignancy") or 0.45) > 1 else float(node.get("poignancy") or 0.45)
        agent.memory.add(0, node.get("type", "memory"), desc, max(0.35, min(0.95, poignancy)), keywords)


def attach_original_relations(agents: Dict[str, Agent], name_to_id: Dict[str, str], folders: List[Path], rng: random.Random) -> None:
    folder_by_name = {json.loads((folder / "bootstrap_memory" / "scratch.json").read_text(encoding="utf-8")).get("name", folder.name): folder for folder in folders if (folder / "bootstrap_memory" / "scratch.json").exists()}
    for source_name, folder in folder_by_name.items():
        source_id = name_to_id.get(source_name)
        if source_id is None:
            continue
        scratch = json.loads((folder / "bootstrap_memory" / "scratch.json").read_text(encoding="utf-8"))
        friends = scratch.get("friends", {})
        for rel_type, names in friends.items():
            for target_name in names:
                target_id = name_to_id.get(target_name)
                if target_id is None or target_id == source_id:
                    continue
                trust = {
                    "best_friends": 0.86,
                    "good_friends": 0.74,
                    "colleague": 0.68,
                    "former_student": 0.62,
                    "complex": 0.45,
                    "tensions": 0.28,
                }.get(rel_type, 0.55)
                agents[source_id].relations[target_id] = SocialRelation(target_id, rel_type, trust + rng.uniform(-0.05, 0.05))
                agents[target_id].relations.setdefault(source_id, SocialRelation(source_id, rel_type, trust + rng.uniform(-0.05, 0.05)))


def strengthen_relation(agents: Dict[str, Agent], name_to_id: Dict[str, str], source_name: str, target_name: str, rel_type: str, trust: float) -> None:
    source_id = name_to_id.get(source_name)
    target_id = name_to_id.get(target_name)
    if source_id is None or target_id is None:
        return
    agents[source_id].relations[target_id] = SocialRelation(target_id, rel_type, trust)
    agents[target_id].relations[source_id] = SocialRelation(source_id, rel_type, trust)


def attach_expert_relations(agents: Dict[str, Agent]) -> None:
    name_to_id = {agent.name: aid for aid, agent in agents.items()}
    relation_rows = [
        ("\u8d75\u660e\u8f69", "\u6797\u5c0f\u96e8", "\u5de5\u4f5c\u8054\u7cfb", 0.66),
        ("\u8d75\u660e\u8f69", "\u674e\u5927\u5f3a", "\u6295\u8bc9\u5bf9\u63a5", 0.52),
        ("\u9648\u7acb\u8861", "\u738b\u4e3d\u534e", "\u98df\u5b89\u68c0\u67e5\u719f\u4eba", 0.61),
        ("\u9648\u7acb\u8861", "\u5218\u5c0f\u654f", "\u73b0\u573a\u7ec6\u8282\u6838\u5bf9", 0.58),
        ("\u5b59\u5b81", "\u6797\u5c0f\u96e8", "\u516c\u536b\u534f\u4f5c", 0.70),
        ("\u5b59\u5b81", "\u5218\u5c0f\u654f", "\u98ce\u9669\u6c9f\u901a", 0.56),
        ("\u5510\u6653\u8212", "\u738b\u4e3d\u534e", "\u793e\u533a\u534f\u8c03", 0.72),
        ("\u5510\u6653\u8212", "\u5f20\u56fd\u5e86", "\u793e\u533a\u4f20\u8bdd", 0.63),
        ("\u5510\u6653\u8212", "\u8d75\u660e\u8f69", "\u4f1a\u8bae\u534f\u8c03", 0.68),
        ("\u5510\u6653\u8212", "\u5b59\u5b81", "\u4f1a\u8bae\u534f\u8c03", 0.68),
        ("\u5510\u6653\u8212", "\u9648\u7acb\u8861", "\u4f1a\u8bae\u534f\u8c03", 0.68),
    ]
    for source_name, target_name, rel_type, trust in relation_rows:
        strengthen_relation(agents, name_to_id, source_name, target_name, rel_type, trust)


def build_town_edges(agents: Dict[str, Agent]) -> Set[Tuple[str, str]]:
    ids = list(agents.keys())
    edges = set()
    for aid, agent in agents.items():
        for target in agent.relations:
            edges.add(pair(aid, target))
    # Small-world ring fallback so the town remains connected.
    n = len(ids)
    for i in range(n):
        edges.add(pair(ids[i], ids[(i + 1) % n]))
        edges.add(pair(ids[i], ids[(i + 2) % n]))
    return edges


def build_community_edges(agents: Dict[str, Agent], rng: random.Random) -> Set[Tuple[str, str]]:
    ids = list(agents.keys())
    edges: Set[Tuple[str, str]] = set()
    by_community: Dict[int, List[str]] = defaultdict(list)
    for aid, agent in agents.items():
        by_community[agent.community].append(aid)

    for members in by_community.values():
        for i, aid in enumerate(members):
            for target in members[i + 1:]:
                edges.add(pair(aid, target))

    for aid, agent in agents.items():
        for target_id, relation in agent.relations.items():
            same_community = agent.community == agents[target_id].community
            if same_community or relation.trust_score >= 0.66:
                edges.add(pair(aid, target_id))
            elif relation.trust_score >= 0.48 and rng.random() < 0.35:
                edges.add(pair(aid, target_id))

    communities = sorted(by_community)
    for i, community in enumerate(communities):
        source = max(by_community[community], key=lambda aid: len(agents[aid].relations))
        target_community = communities[(i + 1) % len(communities)]
        target = max(by_community[target_community], key=lambda aid: len(agents[aid].relations))
        edges.add(pair(source, target))

    n = len(ids)
    if n > 1:
        for i, aid in enumerate(ids):
            if len([x for x in edges if aid in x]) == 0:
                edges.add(pair(aid, ids[(i + 1) % n]))
    return edges


class AnalysisEngine:
    def __init__(self, agents: Dict[str, Agent], edges: Set[Tuple[str, str]], adjacency: Dict[str, Set[str]]):
        self.agents = agents
        self.edges = edges
        self.adjacency = adjacency

    def update_indices(self):
        max_degree = max((len(v) for v in self.adjacency.values()), default=1) or 1
        for agent in self.agents.values():
            neighbors = self.adjacency[agent.id]
            neighbor_pressure = sum(max(0, self.agents[n].stance) for n in neighbors) / max(1, len(neighbors))
            trusted_pressure = 0
            for n in neighbors:
                rel = agent.relations.get(n)
                trusted_pressure += max(0, self.agents[n].stance) * (rel.trust_score if rel else 0.5)
            trusted_pressure /= max(1, len(neighbors))
            cross = len([n for n in neighbors if self.agents[n].community != agent.community]) / max(1, len(neighbors))
            agent.osi = clamp(0.32 * neighbor_pressure + 0.26 * trusted_pressure + 0.18 * agent.arousal + 0.14 * agent.anxiety + 0.10 * (1 - agent.trust))
            agent.cpi = clamp(0.36 * (len(neighbors) / max_degree) + 0.24 * cross + 0.20 * (agent.network_role == "bridge_connector") + 0.20 * (len(agent.relations) / max_degree))
            agent.activation_threshold = clamp(0.55 - 0.20 * agent.osi - 0.15 * ((agent.arousal + agent.anxiety + agent.anger) / 3) + 0.15 * agent.skepticism - 0.10 * agent.cpi)

    def report(self, time_step: int, speeches: List[dict]) -> dict:
        states = defaultdict(int)
        for agent in self.agents.values():
            states[agent.state] += 1
        avg_osi = statistics.mean(a.osi for a in self.agents.values())
        avg_cpi = statistics.mean(a.cpi for a in self.agents.values())
        avg_emotion = statistics.mean((a.arousal + a.anxiety + a.anger) / 3 for a in self.agents.values())
        key_nodes = self.key_nodes()
        state_counts = {STATE_LABELS.get(key, key): value for key, value in states.items()}
        return {
            "timeStep": time_step,
            "overview": f"\u672c\u8f6e\u793e\u533a\u7f51\u7edc\u4e2d\uff0c\u4ea4\u6d41 {states['TALKING']} \u4eba\uff0c\u8d28\u7591 {states['QUESTIONING']} \u4eba\uff0c\u8f9f\u8c23 {states['DEBUNKING']} \u4eba\uff0c\u6c89\u9ed8 {states['SILENT']} \u4eba\u3002",
            "networkMetrics": {"nodeCount": len(self.agents), "edgeCount": len(self.edges), "averageDegree": round(sum(len(v) for v in self.adjacency.values()) / len(self.agents), 2), "averageOsi": round(avg_osi, 3), "averageCpi": round(avg_cpi, 3), "averageEmotion": round(avg_emotion, 3), "clustering": round(self.clustering(), 3), "modularityProxy": round(self.modularity_proxy(), 3)},
            "coefficients": self.coefficients(),
            "emotionTrend": f"\u5e73\u5747\u60c5\u7eea {avg_emotion:.2f}\uff0c\u5e73\u5747 OSI {avg_osi:.2f}\uff0c\u5e73\u5747 CPI {avg_cpi:.2f}\u3002",
            "keyNodes": key_nodes,
            "riskLevel": "\u4e2d" if avg_emotion > 0.38 or avg_osi > 0.45 else "\u4f4e",
            "stateCounts": state_counts,
            "researchRecords": self.research_records(speeches, key_nodes),
            "reflectionDigest": self.reflections(),
            "markdownReport": self.markdown(time_step, speeches, key_nodes, avg_osi, avg_cpi, avg_emotion),
            "modelConstraints": {
                "modelName": "Community-aware Weighted Complex Threshold Model",
                "activationRule": "H_i(t) >= theta_i",
                "intraCommunityWeight": 1.0,
                "interCommunityWeight": 0.45,
                "bridgeBonus": 1.3,
            },
        }

    def key_nodes(self):
        ranked = sorted(self.agents.values(), key=lambda a: len(self.adjacency[a.id]) * 0.45 + a.cpi * 5 + a.osi * 3, reverse=True)
        return [a.id for a in ranked[:6]]

    def coefficients(self):
        return sorted([{"id": a.id, "name": a.name, "personaType": a.persona_type, "emotion": round((a.arousal + a.anxiety + a.anger) / 3, 3), "osi": round(a.osi, 3), "cpi": round(a.cpi, 3), "threshold": round(a.activation_threshold, 3), "pressure": round(a.activation_pressure, 3), "state": STATE_LABELS[a.state]} for a in self.agents.values()], key=lambda x: x["emotion"] + x["osi"] + x["cpi"], reverse=True)

    def research_records(self, speeches, key_nodes):
        key_set = set(key_nodes)
        recent = [s for s in speeches[-20:] if s.get("includedInReport")]
        node_rows = []
        for aid in key_nodes:
            agent = self.agents[aid]
            node_rows.append({
                "id": aid,
                "name": agent.name,
                "degree": len(self.adjacency[aid]),
                "osi": round(agent.osi, 3),
                "cpi": round(agent.cpi, 3),
                "emotion": round((agent.arousal + agent.anxiety + agent.anger) / 3, 3),
                "pressure": round(agent.activation_pressure, 3),
                "threshold": round(agent.activation_threshold, 3),
                "persona": agent.persona_type,
                "memory": agent.memory.associative[-1].content if agent.memory.associative else "",
            })
        evidence = []
        for item in recent[-10:]:
            touches_key = item.get("agentId") in key_set or bool(key_set.intersection(item.get("receivers", [])))
            evidence.append({
                "timeStep": item.get("timeStep"),
                "speaker": item.get("agentName"),
                "receivers": item.get("receiverNames", []),
                "actionType": item.get("actionType"),
                "content": item.get("content"),
                "emotion": item.get("emotionIntensity"),
                "osi": item.get("osi"),
                "cpi": item.get("cpi"),
                "touchesKeyNode": touches_key,
            })
        return {"keyNodeTable": node_rows, "dialogueEvidence": evidence}

    def reflections(self):
        items = []
        for agent in self.agents.values():
            items.extend(node.content for node in agent.memory.reflections[-2:])
        return items[-8:] or ["\u5c1a\u672a\u7d2f\u79ef\u8db3\u591f\u5bf9\u8bdd\u89e6\u53d1\u6d1e\u5bdf\u53cd\u601d\u3002"]

    def clustering(self):
        vals = []
        for node, neighbors in self.adjacency.items():
            ns = list(neighbors)
            if len(ns) < 2:
                continue
            links = sum(1 for i in range(len(ns)) for j in range(i + 1, len(ns)) if ns[j] in self.adjacency[ns[i]])
            vals.append(2 * links / (len(ns) * (len(ns) - 1)))
        return statistics.mean(vals) if vals else 0.0

    def modularity_proxy(self):
        if not self.edges:
            return 0.0
        internal = sum(1 for a, b in self.edges if self.agents[a].community == self.agents[b].community)
        return internal / len(self.edges)

    def markdown(self, time_step, speeches, key_nodes, avg_osi, avg_cpi, avg_emotion):
        recent = [x for x in speeches[-12:] if x.get("includedInReport")]
        examples = "\n".join([f"- T{x['timeStep']} {x['agentName']} -> {', '.join(x['receiverNames'])}: {x['content']}" for x in recent[-6:]]) or "- \u5c1a\u65e0\u5bf9\u8bdd\u8bc1\u636e"
        key_table = "\n".join([f"- {aid}: {self.agents[aid].name}, degree={len(self.adjacency[aid])}, OSI={self.agents[aid].osi:.3f}, CPI={self.agents[aid].cpi:.3f}" for aid in key_nodes])
        return f"""# \u793e\u533a\u7f51\u7edc\u4f20\u64ad\u89e3\u91ca

## \u4e3a\u4ec0\u4e48\u662f\u8fd9\u4e2a\u7ed3\u679c
\u672c\u6b21\u542f\u7528\u793e\u533a\u7f51\u7edc\uff0c\u4f7f\u7528\u539f\u59cb\u5c0f\u9547 Agent \u7684\u4eba\u8bbe\u3001\u670b\u53cb\u5173\u7cfb\u548c\u8bb0\u5fc6\u3002\u4f20\u64ad\u52a8\u529b\u5b66\u91c7\u7528\u793e\u533a\u52a0\u6743\u590d\u6742\u9608\u503c\u6a21\u578b\uff1a\u7f51\u7edc\u7ed3\u6784\u51b3\u5b9a\u53ef\u5bf9\u8bdd\u5bf9\u8c61\uff0c\u5f71\u54cd\u538b\u529b H_i(t) \u4e0e\u4e2a\u4f53\u9608\u503c theta_i \u51b3\u5b9a\u662f\u5426\u88ab\u6fc0\u6d3b\uff0c\u793e\u533a\u5185\u6743\u91cd\u9ad8\u4e8e\u793e\u533a\u95f4\u6743\u91cd\uff0c\u6865\u63a5\u8282\u70b9\u83b7\u5f97\u7834\u5708\u52a0\u6743\u3002\u8a00\u8bba\u5185\u5bb9\u4ecd\u6765\u81ea\u8bf4\u8bdd\u8005\u7684\u4eba\u8bbe\u3001\u5f53\u524d\u72b6\u6001\u3001\u68c0\u7d22\u5230\u7684\u8bb0\u5fc6\u548c\u5bf9\u8bdd\u5bf9\u8c61\u3002

## \u53ef\u7528\u4e8e\u8bba\u6587\u7684\u5173\u952e\u6307\u6807
- \u65f6\u95f4\u6b65\uff1a{time_step}
- \u5e73\u5747 OSI\uff1a{avg_osi:.3f}
- \u5e73\u5747 CPI\uff1a{avg_cpi:.3f}
- \u5e73\u5747\u60c5\u7eea\uff1a{avg_emotion:.3f}
- \u6fc0\u6d3b\u89c4\u5219\uff1aH_i(t) >= theta_i
- \u793e\u533a\u5185\u6743\u91cd\uff1a1.0
- \u793e\u533a\u95f4\u6743\u91cd\uff1a0.45
- \u6865\u63a5\u8282\u70b9\u52a0\u6743\uff1a1.3

## \u5173\u952e\u8282\u70b9\u8868
{key_table}

## \u8bc1\u636e\uff1a\u8fd1\u671f\u5bf9\u8bdd
{examples}

## \u53cd\u9ed1\u7bb1\u8bf4\u660e
\u7cfb\u7edf\u4e0d\u76f4\u63a5\u8ba9\u6240\u6709 Agent \u540c\u65f6\u8868\u6001\uff0c\u800c\u662f\u5148\u7531\u793e\u533a\u7f51\u7edc\u7ed3\u6784\u7ea6\u675f\u5019\u9009\u5bf9\u8bdd\u8fb9\uff0c\u518d\u7528\u590d\u6742\u9608\u503c\u6a21\u578b\u5224\u65ad\u6fc0\u6d3b\u538b\u529b\uff0c\u6700\u540e\u7531 Agent \u4eba\u8bbe\u4e0e\u8bb0\u5fc6\u751f\u6210\u5bf9\u8bdd\u3002\u56e0\u6b64\u53ef\u4ee5\u901a\u8fc7\u6bcf\u6761\u5bf9\u8bdd\u3001\u6bcf\u4e2a\u8282\u70b9\u7684 H_i/theta_i/OSI/CPI \u548c\u8bb0\u5fc6\u6458\u8981\u89e3\u91ca\u4f20\u64ad\u8def\u5f84\u3002"""


class SimulationEngine:
    def __init__(self, network_type: str = "community_network", seed: Optional[int] = None):
        self.rng = random.Random(seed if seed is not None else 20260510)
        self.network_type = network_type if network_type in NETWORK_SCENARIOS else "community_network"
        self.config = NETWORK_SCENARIOS[self.network_type]
        self.agents = load_original_agents(self.rng)
        self.edges = build_community_edges(self.agents, self.rng)
        self.adjacency = self._adjacency(self.edges)
        self._assign_network_roles()
        self.time_step = 0
        self.active_flows = []
        self.speeches = []
        self.pair_cooldown: Dict[Tuple[str, str], int] = {}
        self.analysis = AnalysisEngine(self.agents, self.edges, self.adjacency)
        self._seed_event()
        self.analysis.update_indices()
        self.report = self.analysis.report(self.time_step, self.speeches)

    def step(self, intervention=None):
        self.time_step += 1
        self.active_flows = []
        self.analysis.update_indices()
        pairs = self._conversation_pairs()
        if intervention:
            self._intervene(intervention)
        for source_id, target_id in pairs:
            source, target = self.agents[source_id], self.agents[target_id]
            action = self._decide(source, target)
            content = self._generate_dialogue(source, target, action)
            self._record_dialogue(source, target, action, content)
            self._receive(target, source, action, content)
            self.active_flows.append({"id": str(uuid.uuid4()), "source": source.id, "target": target.id, "actionType": action})
            if action != "ignore" and self.rng.random() < 0.68:
                reply = self._generate_reply(target, source, content)
                target.state = "TALKING" if target.state in {"UNAWARE", "LISTENING", "SILENT"} else target.state
                self._record_dialogue(target, source, "reply", reply)
                self._receive(source, target, "reply", reply)
                self.active_flows.append({"id": str(uuid.uuid4()), "source": target.id, "target": source.id, "actionType": "reply"})
            insight = source.memory.reflect(self.time_step, source, self.adjacency)
            if insight:
                self._record_reflection(source, insight)
        self.analysis.update_indices()
        self.report = self.analysis.report(self.time_step, self.speeches)
        return self.snapshot()

    def snapshot(self):
        return {"networkType": self.network_type, "sceneName": self.config["scene_name"], "model": self.config["model"], "description": self.config["description"], "timeStep": self.time_step, "nodes": [self._agent_payload(a) for a in self.agents.values()], "edges": [self._edge(a, b) for a, b in sorted(self.edges)], "activeFlows": self.active_flows, "speeches": self.speeches[-180:], "report": self.report, "stateLabels": STATE_LABELS, "scenarios": [{"type": key, "label": value["label"], "sceneName": value["scene_name"], "model": value["model"]} for key, value in NETWORK_SCENARIOS.items()]}

    def _agent_payload(self, a: Agent):
        return {"id": a.id, "name": a.name, "personaType": a.persona_type, "networkRole": a.network_role, "community": a.community, "profile": a.profile, "currentState": a.state, "stateLabel": STATE_LABELS[a.state], "emotionScore": round((a.arousal + a.anxiety + a.anger) / 3, 3), "stanceScore": round(a.stance, 3), "osi": round(a.osi, 3), "cpi": round(a.cpi, 3), "pressure": round(a.activation_pressure, 3), "threshold": round(a.activation_threshold, 3), "skepticism": round(a.skepticism, 3), "socialResponsibility": round(a.social_responsibility, 3), "isHub": a.network_role == "bridge_connector", "isBridge": a.network_role == "bridge_connector", "degree": len(self.adjacency[a.id]), "relations": [vars(r) for r in list(a.relations.values())[:10]], "memories": [vars(n) for n in a.memory.associative[-8:]], "reflections": [vars(n) for n in a.memory.reflections[-5:]]}

    def _edge(self, a, b):
        rel = self.agents[a].relations.get(b)
        community_text = "\u793e\u533a\u5185" if self.agents[a].community == self.agents[b].community else "\u8de8\u793e\u533a"
        return {"id": f"{a}-{b}", "source": a, "target": b, "trust": round(rel.trust_score if rel else self.config["default_trust"], 2), "relationType": rel.relation_type if rel else community_text, "communityScope": community_text}

    def _adjacency(self, edges):
        adj = {aid: set() for aid in self.agents}
        for a, b in edges:
            adj[a].add(b)
            adj[b].add(a)
        return adj

    def _assign_network_roles(self):
        for aid, agent in self.agents.items():
            cross_edges = sum(1 for target in self.adjacency[aid] if self.agents[target].community != agent.community)
            degree = len(self.adjacency[aid])
            if cross_edges >= 2 or (cross_edges >= 1 and degree >= 5):
                agent.network_role = "bridge_connector"
            elif degree >= 5:
                agent.network_role = "community_hub"
            else:
                agent.network_role = "community_member"

    def _seed_event(self):
        for aid in self.report_seed_nodes():
            a = self.agents[aid]
            a.state = "EXPOSED"
            a.exposure_count += 1
            a.memory.add(0, "event", "\u542c\u5230\u5173\u4e8e\u5e7c\u513f\u56ed\u98df\u7269\u4e2d\u6bd2\u4e8b\u4ef6\u7684\u65b0\u8bf4\u6cd5\uff0c\u4f46\u7ec6\u8282\u8fd8\u4e0d\u5b8c\u6574\u3002", 0.82, ["event", "rumor"])

    def report_seed_nodes(self):
        ranked = sorted(self.agents.values(), key=lambda a: len(a.relations), reverse=True)
        return [a.id for a in ranked[:3]]

    def _legacy_decide_unused(self, source: Agent, target: Agent):
        rel = source.relations.get(target.id)
        trust = rel.trust_score if rel else 0.55
        memory_pressure = sum(m.poignancy for m in source.memory.retrieve(["event", "rumor", "evidence"], 3)) / 3
        speak = clamp(0.30 + source.cpi * 0.25 + source.arousal * 0.18 + memory_pressure * 0.18 + trust * 0.09)
        verify = clamp(0.15 + (1 - source.trust) * 0.25 + source.osi * 0.15 + ("核" in source.learned or "监督" in source.learned) * 0.25)
        if self.rng.random() > speak:
            source.state = "SILENT"
            return "ignore"
        if self.rng.random() < verify:
            source.state = "QUESTIONING" if source.trust < 0.52 else "DEBUNKING"
            return "question" if source.state == "QUESTIONING" else "debunk"
        source.state = "TALKING"
        return "share"

    def _generate_dialogue(self, source: Agent, target: Agent, action: str):
        llm_line = self._generate_dialogue_with_llm(source, target, action)
        if llm_line:
            return llm_line
        memories = [m for m in source.memory.retrieve(["event", "rumor", "evidence", "intervention"], 5) if m.kind in {"event", "intervention", "evidence"}]
        memory_hint = self._memory_hint(source, memories)
        relation = source.relations.get(target.id)
        rel_text = relation.relation_type if relation else "\u719f\u4eba"
        previous = relation.last_message if relation else ""
        concern = self._agent_concern(source)
        prefix = self._dialogue_prefix(source, target, rel_text)
        line = self._voice_line(source, target, action, memory_hint, concern, previous)
        return f"{prefix}{line}"

    def _generate_dialogue_with_llm(self, source: Agent, target: Agent, action: str) -> Optional[str]:
        if ChatGPT_single_request is None or source.scratch is None:
            return None
        try:
            source.scratch.curr_time = datetime.datetime(2026, 5, 11, 9, 0, 0) + datetime.timedelta(minutes=self.time_step * 5)
            target_profile = target.scratch.get_str_iss() if target.scratch else target.profile
            relation = source.relations.get(target.id)
            relationship = relation.relation_type if relation else "\u666e\u901a\u719f\u4eba"
            retrieved = self._original_retrieved_text(source, target)
            previous = relation.last_message if relation else ""
            action_hint = {
                "share": "\u60f3\u628a\u81ea\u5df1\u77e5\u9053\u6216\u62c5\u5fc3\u7684\u4fe1\u606f\u544a\u8bc9\u5bf9\u65b9",
                "question": "\u60f3\u8ffd\u95ee\u6765\u6e90\u3001\u8bc1\u636e\u6216\u7ec6\u8282",
                "debunk": "\u60f3\u963b\u6b62\u672a\u6838\u5b9e\u4fe1\u606f\u7ee7\u7eed\u6269\u6563",
                "ignore": "\u4e0d\u60f3\u7acb\u523b\u8868\u6001\uff0c\u66f4\u60f3\u89c2\u671b\u6216\u4fdd\u7559",
                "reply": "\u6b63\u5728\u56de\u5e94\u5bf9\u65b9\u521a\u624d\u8bf4\u7684\u8bdd",
            }.get(action, "\u6b63\u5728\u56de\u5e94\u5bf9\u65b9")
            prompt = f"""你在模拟斯坦福 Generative Agents 小镇中的一次真实对话。

要求：
1. 只输出一句中文口语台词，格式为：{source.name}对{target.name}说：“...”
2. 不要写旁白，不要解释人设，不要复述“某某是...的人”。
3. 台词必须符合说话者的人设、记忆、和对对方的关系。
4. 台词要自然、有具体语气，像熟人之间真实说话，不要模板化。
5. 不要每次都问“来源靠谱吗”，除非人物真的会这样问。
6. 长度控制在 25 到 80 个汉字。

说话者身份：
{source.scratch.get_str_iss() if source.scratch else source.profile}

对话对象身份：
{target_profile}

两人关系：{relationship}
当前传播动作：{action_hint}
上一轮相关对话：{previous or "暂无"}

说话者当前可检索到的记忆流内容：
{retrieved}

现在生成这一句台词。"""
            response = self._llm_request(prompt).strip()
            if self._valid_llm_line(response):
                return self._normalize_llm_line(response, source, target)
        except Exception:
            return None
        return None

    def _llm_request(self, prompt: str) -> str:
        base_url = LOCAL_API_BASE if USE_LOCAL_MODEL else DEEPSEEK_API_BASE
        model = LOCAL_MODEL_NAME if USE_LOCAL_MODEL else DEEPSEEK_MODEL_NAME
        api_key = LOCAL_API_KEY if USE_LOCAL_MODEL else deepseek_api_key
        if not base_url or not model:
            return ""
        url = base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.85,
            "top_p": 0.9,
            "max_tokens": 180,
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=35) as response:
                result = json.loads(response.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, json.JSONDecodeError, TimeoutError):
            return ""

    def _original_retrieved_text(self, source: Agent, target: Agent) -> str:
        rows = []
        if source.a_mem:
            for node in (source.a_mem.seq_chat[:3] + source.a_mem.seq_event[:5] + source.a_mem.seq_thought[:5]):
                if target.name in node.description or "食物中毒" in node.description or "幼儿园" in node.description or "证据" in node.description:
                    rows.append(f"- {node.description}")
        if not rows:
            rows = [f"- {node.content}" for node in source.memory.retrieve(["event", "rumor", "evidence", target.name], 5)]
        return "\n".join(rows[:8]) or "- 当前只知道幼儿园食物中毒事件仍有细节未核实。"

    def _valid_llm_line(self, response: str) -> bool:
        bad_markers = ["LLM API ERROR", "\u8fde\u63a5\u9519\u8bef", "\u8d85\u65f6", "无法连接", "[", "]"]
        return bool(response) and not any(marker in response for marker in bad_markers) and len(response) >= 6

    def _normalize_llm_line(self, response: str, source: Agent, target: Agent) -> str:
        response = response.strip().strip('"').strip()
        if "\n" in response:
            response = response.splitlines()[0].strip()
        if f"{source.name}\u5bf9{target.name}\u8bf4" in response:
            return response
        if "\uff1a" in response and response.startswith(source.name):
            return response
        return f"{source.name}\u5bf9{target.name}\u8bf4\uff1a{response}"

    def _memory_hint(self, agent: Agent, memories: List[MemoryNode]) -> str:
        for node in memories:
            content = node.content
            for marker in ["\u8bf4\uff1a", "\u542c\u5230\uff1a", "\uff1a"]:
                if marker in content:
                    content = content.split(marker, 1)[-1]
            content = content.replace(f"{agent.name}\u5bf9", "").strip()
            for repeated in ["\u6211\u8fd8\u662f\u60f3\u518d\u6838\u4e00\u4e0b", "\u6211\u8fd8\u662f\u6709\u70b9\u62ff\u4e0d\u51c6"]:
                content = content.replace(repeated, "")
            content = content.strip("\u3002\uff0c\uff1a: ")
            if len(content) > 12:
                return content[:46]
        return "\u73b0\u5728\u8bf4\u6cd5\u592a\u591a\uff0c\u5f88\u591a\u7ec6\u8282\u8fd8\u5bf9\u4e0d\u4e0a"

    def _dialogue_prefix(self, source: Agent, target: Agent, rel_text: str) -> str:
        relation_words = {
            "best_friends": "\u538b\u4f4e\u58f0\u97f3",
            "good_friends": "\u8ba4\u771f\u5730",
            "tensions": "\u5fCD\u7740\u60c5\u7eea",
            "potential_conflict": "\u8bed\u6c14\u6709\u70b9\u51b2",
            "\u6295\u8bc9\u5bf9\u63a5": "\u5c3d\u91cf\u653e\u6162\u8bed\u901f",
            "\u4f1a\u8bae\u534f\u8c03": "\u4e00\u8fb9\u8bb0\u5f55\u4e00\u8fb9",
        }
        tone = relation_words.get(rel_text, "\u5bf9")
        if tone == "\u5bf9":
            return f"{source.name}\u5bf9{target.name}\u8bf4\uff1a"
        return f"{source.name}{tone}\u5bf9{target.name}\u8bf4\uff1a"

    def _agent_concern(self, agent: Agent) -> str:
        concern_map = {
            "\u674e\u5927\u5f3a": "\u6211\u5b69\u5b50\u8fd8\u5728\u533b\u9662\uff0c\u6211\u8981\u7684\u4e0d\u662f\u597d\u542c\u8bdd\uff0c\u662f\u4e00\u4e2a\u8bf4\u5f97\u6e05\u7684\u7ed3\u679c",
            "\u6797\u5c0f\u96e8": "\u6211\u4e0d\u60f3\u8ba9\u5bb6\u957f\u89c9\u5f97\u6211\u4eec\u5728\u8eb2\uff0c\u4f46\u5b69\u5b50\u5148\u8981\u7a33\u4f4f",
            "\u5218\u5c0f\u654f": "\u6709\u4e9b\u7ec6\u8282\u6211\u771f\u7684\u770b\u5230\u4e86\uff0c\u53ef\u6211\u73b0\u5728\u4e00\u5f20\u53e3\u5c31\u5bb3\u6015",
            "\u738b\u4e3d\u534e": "\u6211\u5496\u5561\u9986\u91cc\u6bcf\u4e2a\u4eba\u90fd\u5728\u95ee\uff0c\u8bf4\u9519\u4e00\u53e5\u5c31\u80fd\u4f20\u4e00\u6761\u8857",
            "\u9648\u601d\u8fdc": "\u8fd9\u4ef6\u4e8b\u4e0d\u53ea\u662f\u8c01\u9053\u6b49\uff0c\u662f\u6211\u4eec\u5230\u5e95\u600e\u4e48\u770b\u5f85\u5b69\u5b50\u7684\u5b89\u5168",
            "\u9ad8\u5efa\u56fd": "\u522b\u53c8\u662f\u4e00\u5957\u6f02\u4eae\u8bdd\uff0c\u6700\u540e\u4ec0\u4e48\u4eba\u90fd\u4e0d\u7528\u8d1f\u8d23",
            "\u97e9\u5c0f\u96ea": "\u6211\u4ee5\u524d\u4e5f\u5728\u90a3\u91cc\u5403\u8fc7\u996d\uff0c\u6240\u4ee5\u542c\u5230\u7684\u65f6\u5019\u5fc3\u91cc\u4e00\u76f4\u53d1\u51b7",
            "\u5468\u5c0f\u827a": "\u6211\u5148\u628a\u770b\u5230\u548c\u542c\u5230\u7684\u8bb0\u4e0b\u6765\uff0c\u4e0d\u60f3\u628a\u522b\u4eba\u7684\u5bb3\u6015\u753b\u6210\u70ed\u95f9",
            "\u5f20\u56fd\u5e86": "\u6211\u8f66\u4e0a\u542c\u4e86\u592a\u591a\u7248\u672c\uff0c\u8d8a\u542c\u8d8a\u89c9\u5f97\u5f97\u628a\u65f6\u95f4\u7ebf\u7406\u6e05",
            "\u8d75\u660e\u8f69": "\u6211\u77e5\u9053\u5927\u5bb6\u5acc\u6d41\u7a0b\u6162\uff0c\u4f46\u4e0d\u628a\u65f6\u95f4\u7ebf\u6838\u5b9e\u6e05\u695a\uff0c\u540e\u9762\u66f4\u6ca1\u6cd5\u8d1f\u8d23",
            "\u9648\u7acb\u8861": "\u6211\u53ea\u770b\u5355\u636e\u3001\u7559\u6837\u548c\u8fdb\u8d27\u8bb0\u5f55\uff0c\u54ea\u4e00\u73af\u5bf9\u4e0d\u4e0a\u5c31\u4e0d\u80fd\u653e\u8fc7",
            "\u5b59\u5b81": "\u5bb6\u957f\u5bb3\u6015\u662f\u6b63\u5e38\u7684\uff0c\u4f46\u6211\u4eec\u8981\u628a\u75c7\u72b6\u3001\u5c31\u533b\u548c\u98df\u7269\u7ebf\u7d22\u5206\u5f00",
            "\u5510\u6653\u8212": "\u6211\u5148\u628a\u6bcf\u4e2a\u4eba\u7684\u7591\u95ee\u8bb0\u4e0b\u6765\uff0c\u4e0d\u7136\u4f1a\u8bae\u53ea\u4f1a\u53d8\u6210\u4e92\u76f8\u5435",
        }
        return concern_map.get(agent.name, "\u8fd9\u4ef6\u4e8b\u8fd8\u6709\u5f88\u591a\u6ca1\u8bf4\u6e05\u7684\u5730\u65b9")

    def _voice_line(self, source: Agent, target: Agent, action: str, memory_hint: str, concern: str, previous: str) -> str:
        name = source.name
        if action == "ignore":
            return self._silent_line(source, target, concern)
        style_bank = {
            "\u9648\u601d\u8fdc": {
                "share": [f"\u6211\u5728\u60f3\uff0c{memory_hint}\u8fd9\u4e2a\u7247\u6bb5\u4e3a\u4ec0\u4e48\u4f1a\u8ba9\u5927\u5bb6\u8fd9\u4e48\u5feb\u5c31\u76f8\u4fe1\u3002{concern}\u3002"],
                "question": [f"\u4e3d\u534e\uff0c\u6211\u4e0d\u662f\u5426\u5b9a\u4f60\u542c\u5230\u7684\u8bdd\u3002\u6211\u53ea\u662f\u60f3\u95ee\uff0c\u8fd9\u4e2a\u8bf4\u6cd5\u662f\u4e8b\u5b9e\uff0c\u8fd8\u662f\u5927\u5bb6\u7684\u6050\u60e7\u5728\u4e92\u76f8\u627e\u56de\u58f0\uff1f", f"\u6211\u4eec\u5148\u522b\u628a\u5b83\u53d8\u6210\u7ed3\u8bba\u3002{memory_hint}\u8fd9\u91cc\u9762\u81f3\u5c11\u8fd8\u5dee\u4e00\u4e2a\u80fd\u88ab\u6838\u5bf9\u7684\u73af\u8282\u3002"],
                "debunk": [f"\u5982\u679c\u6ca1\u6709\u8bc1\u636e\uff0c\u8fd9\u53e5\u8bdd\u53ea\u4f1a\u628a\u7126\u8651\u53d8\u6210\u4e00\u79cd\u66f4\u6709\u6740\u4f24\u529b\u7684\u53d9\u4e8b\u3002\u5148\u505c\u4e00\u4e0b\u3002"],
            },
            "\u6797\u5c0f\u96e8": {
                "share": [f"\u6211\u4eca\u5929\u53c8\u628a\u51e0\u4e2a\u5bb6\u957f\u7684\u8bdd\u5bf9\u4e86\u4e00\u904d\uff0c{memory_hint}\u3002\u6211\u771f\u7684\u60f3\u5e2e\u5b69\u5b50\u5148\u7a33\u4f4f\u3002"],
                "question": [f"\u8fd9\u4e2a\u6211\u5f97\u518d\u95ee\u4e00\u4e0b\u3002\u4e0d\u662f\u6211\u4e0d\u76f8\u4fe1\u4f60\uff0c\u662f\u6211\u4eec\u73b0\u5728\u6bcf\u53e5\u8bdd\u90fd\u4f1a\u88ab\u5bb6\u957f\u53cd\u590d\u770b\u3002"],
                "debunk": [f"\u8fd9\u53e5\u5148\u522b\u4f20\uff0c\u771f\u7684\u3002\u73b0\u5728\u5bb6\u957f\u5df2\u7ecf\u591f\u614c\u4e86\uff0c\u6211\u4eec\u4e0d\u80fd\u518d\u628a\u6ca1\u6838\u5b9e\u7684\u8bdd\u63a8\u7ed9\u4ed6\u4eec\u3002"],
            },
            "\u5218\u5c0f\u654f": {
                "share": [f"\u6211\u53ea\u80fd\u5c0f\u58f0\u8bf4\u3002{memory_hint}\u3002\u6211\u4e0d\u77e5\u9053\u8fd9\u7b97\u4e0d\u7b97\u8bc1\u636e\uff0c\u4f46\u6211\u5fc3\u91cc\u4e00\u76f4\u8fc7\u4e0d\u53bb\u3002"],
                "question": [f"\u5c0f\u96e8\uff0c\u4f60\u80fd\u5148\u522b\u8ddf\u522b\u4eba\u8bf4\u662f\u6211\u95ee\u7684\u5417\uff1f\u6211\u60f3\u786e\u8ba4\u4e00\u4e0b\uff0c{memory_hint}\u8fd9\u4e2a\u7ec6\u8282\u5230\u5e95\u6709\u6ca1\u6709\u4eba\u8bb0\u5f55\u3002"],
                "debunk": [f"\u8fd9\u4e2a\u4e0d\u5bf9\u3002\u6211\u4e0d\u6562\u8bf4\u592a\u591a\uff0c\u4f46\u8fd9\u53e5\u548c\u6211\u90a3\u5929\u770b\u5230\u7684\u4e0d\u4e00\u6837\u3002"],
            },
            "\u674e\u5927\u5f3a": {
                "share": [f"\u56fd\u5e86\uff0c\u6211\u4eca\u5929\u53c8\u542c\u5230\u4e00\u4e2a\u8bf4\u6cd5\uff0c{memory_hint}\u3002{concern}\u3002", f"\u4f60\u522b\u5acc\u6211\u8bf4\u8bdd\u51b2\uff0c{memory_hint}\u3002\u6211\u73b0\u5728\u5c31\u60f3\u77e5\u9053\u8c01\u80fd\u628a\u8fd9\u4e8b\u8bf4\u6e05\u695a\u3002"],
                "question": [f"\u4f60\u8fd9\u8bdd\u662f\u542c\u8c01\u8bf4\u7684\uff1f{memory_hint}\u8fd9\u79cd\u8bdd\u522b\u53c8\u8ba9\u5bb6\u957f\u767d\u7b49\u4e00\u573a\u3002"],
                "debunk": [f"\u5148\u522b\u8f6c\u4e86\uff0c\u6ca1\u6709\u767d\u7eb8\u9ed1\u5b57\u7684\u8bc1\u636e\uff0c\u6211\u4e0d\u8ba4\u3002{concern}\u3002"],
            },
            "\u5468\u5c0f\u827a": {
                "share": [f"\u6211\u521a\u521a\u53ea\u662f\u542c\u5230\u4e00\u70b9\uff1a{memory_hint}\u3002\u6211\u4e0d\u786e\u5b9a\uff0c\u4f46\u8fd9\u4e2a\u753b\u9762\u4e00\u76f4\u5728\u6211\u8111\u5b50\u91cc\u3002"],
                "question": [f"{target.name}\uff0c\u8fd9\u4e2a\u6765\u6e90\u80fd\u518d\u95ee\u4e00\u4e0b\u5417\uff1f\u6211\u6015\u6211\u4eec\u628a\u5bb3\u6015\u5f53\u6210\u4e86\u4e8b\u5b9e\u3002"],
                "debunk": [f"\u6211\u5148\u4e0d\u628a\u8fd9\u53e5\u8bdd\u653e\u5230\u753b\u91cc\uff0c\u56e0\u4e3a\u5b83\u8fd8\u6ca1\u6709\u8bc1\u636e\u3002"],
            },
            "\u97e9\u5c0f\u96ea": {
                "share": [f"\u6211\u5728\u73ed\u7ea7\u7fa4\u91cc\u770b\u5230\u4e86\u4e00\u70b9\uff0c{memory_hint}\u3002\u6211\u4e0d\u6562\u8f6c\uff0c\u4f46\u6211\u4e00\u76f4\u5728\u60f3\u4ee5\u524d\u98df\u5802\u7684\u5473\u9053\u3002"],
                "question": [f"\u8fd9\u4e2a\u771f\u7684\u5417\uff1f\u6211\u4e0d\u60f3\u88ab\u5927\u4eba\u8bf4\u2018\u5c0f\u5b69\u5b50\u522b\u7ba1\u2019\uff0c\u4f46\u6211\u4e5f\u4e0d\u60f3\u628a\u9519\u7684\u8bdd\u53d1\u7ed9\u540c\u5b66\u3002"],
                "debunk": [f"\u8fd9\u6761\u6211\u4e0d\u8f6c\u3002\u5982\u679c\u662f\u5047\u7684\uff0c\u90a3\u4e9b\u8fd8\u5728\u533b\u9662\u7684\u5c0f\u5b69\u5b50\u4f1a\u66f4\u96be\u8fc7\u5427\u3002"],
            },
            "\u5f20\u56fd\u5e86": {
                "share": [f"\u5927\u5f3a\uff0c\u6211\u8f66\u4e0a\u8fd9\u51e0\u5929\u8f7d\u8fc7\u4e0d\u5c11\u5bb6\u957f\u3002{memory_hint}\u3002\u6211\u4e0d\u6562\u8bf4\u5168\u662f\u771f\u7684\uff0c\u4f46\u5927\u5bb6\u771f\u7684\u90fd\u614c\u4e86\u3002"],
                "question": [f"\u8fd9\u8bdd\u6211\u5f97\u95ee\u6e05\u695a\uff0c\u662f\u4f60\u4eb2\u773c\u770b\u5230\u7684\uff0c\u8fd8\u662f\u522b\u4eba\u5728\u8f66\u4e0a\u8ddf\u6211\u8bf4\u7684\uff1f\u6211\u73b0\u5728\u4e0d\u6562\u518d\u628a\u6545\u4e8b\u8bb2\u6b6a\u4e86\u3002"],
                "debunk": [f"\u8fd9\u4e2a\u7248\u672c\u6211\u542c\u8fc7\uff0c\u4f46\u524d\u540e\u5bf9\u4e0d\u4e0a\u3002\u5148\u522b\u5f80\u4e0b\u4f20\uff0c\u4e0d\u7136\u8d8a\u8bb2\u8d8a\u50cf\u771f\u7684\u3002"],
            },
            "\u738b\u4e3d\u534e": {
                "share": [f"\u54ce\u4f60\u542c\u6211\u8bf4\uff0c\u4eca\u5929\u5e97\u91cc\u53c8\u6709\u4eba\u63d0\u5230\uff1a{memory_hint}\u3002\u6211\u73b0\u5728\u771f\u4e0d\u6562\u968f\u4fbf\u63a5\u8bdd\u4e86\u3002"],
                "question": [f"\u7b49\u7b49\uff0c\u8fd9\u4e2a\u662f\u5bb6\u957f\u8bf4\u7684\uff0c\u8fd8\u662f\u7fa4\u91cc\u8f6c\u7684\uff1f\u6211\u6015\u6211\u4e00\u5f20\u5634\u53c8\u7ed9\u4f20\u5927\u4e86\u3002"],
                "debunk": [f"\u8fd9\u6761\u5148\u522b\u5728\u6211\u5e97\u91cc\u4f20\uff0c\u6ca1\u6838\u5bf9\u524d\u5c31\u8bf4\u51fa\u53bb\uff0c\u5bb6\u957f\u66f4\u614c\u3002"],
            },
            "\u9ad8\u5efa\u56fd": {
                "share": [f"\u6211\u5c31\u8bf4\u5427\uff0c{memory_hint}\u3002\u6700\u540e\u522b\u53c8\u662f\u51e0\u53e5\u573a\u9762\u8bdd\u628a\u4eba\u6253\u53d1\u4e86\u3002"],
                "question": [f"\u8fd9\u8bdd\u542c\u7740\u50cf\u771f\u7684\uff0c\u4f46\u54ea\u6765\u7684\uff1f\u522b\u53c8\u662f\u8bc4\u8bba\u533a\u7f16\u51fa\u6765\u9a82\u4eba\u7684\u3002"],
                "debunk": [f"\u8fd9\u6761\u6211\u5148\u4e0d\u9a82\uff0c\u6ca1\u8bc1\u636e\u9a82\u9519\u4eba\u4e5f\u591f\u6076\u5fc3\u7684\u3002"],
            },
            "\u8d75\u660e\u8f69": {
                "share": [f"\u6211\u5148\u8bf4\u6211\u80fd\u786e\u8ba4\u7684\u90e8\u5206\uff1a{memory_hint}\u3002\u5176\u4ed6\u7ec6\u8282\u8fd8\u8981\u548c\u8bb0\u5f55\u8868\u5bf9\u4e00\u904d\u3002"],
                "question": [f"\u8fd9\u4e2a\u8bf4\u6cd5\u9700\u8981\u6709\u5bf9\u5e94\u65f6\u95f4\u548c\u8bb0\u5f55\uff0c\u4e0d\u7136\u6211\u4e0d\u80fd\u628a\u5b83\u5199\u8fdb\u7ed3\u8bba\u91cc\u3002"],
                "debunk": [f"\u8fd9\u6761\u4e0d\u80fd\u518d\u6269\u6563\u3002\u73b0\u5728\u80fd\u8bf4\u7684\u662f\u6838\u67e5\u8303\u56f4\uff0c\u4e0d\u662f\u6700\u7ec8\u5b9a\u6027\u3002"],
            },
            "\u9648\u7acb\u8861": {
                "share": [f"\u6211\u8fd9\u8fb9\u53ea\u770b\u5230\u4e00\u4e2a\u7ebf\u7d22\uff1a{memory_hint}\u3002\u522b\u5148\u731c\uff0c\u5148\u628a\u5355\u636e\u548c\u7559\u6837\u627e\u51fa\u6765\u3002"],
                "question": [f"\u8fd9\u53e5\u8bdd\u6ca1\u7528\uff0c\u6709\u6ca1\u6709\u8fdb\u8d27\u65f6\u95f4\u3001\u6279\u6b21\u548c\u7559\u6837\uff1f\u6ca1\u6709\u5c31\u53ea\u80fd\u5148\u6302\u8d77\u6765\u3002"],
                "debunk": [f"\u8fd9\u4e2a\u5224\u65ad\u592a\u65e9\u3002\u6211\u6ca1\u770b\u5230\u68c0\u6d4b\u548c\u7968\u636e\u524d\uff0c\u4e0d\u8ba9\u5b83\u5f53\u7ed3\u8bba\u4f20\u3002"],
            },
            "\u5b59\u5b81": {
                "share": [f"\u6211\u60f3\u5148\u628a\u60c5\u7eea\u653e\u6162\u4e00\u70b9\u3002{memory_hint}\u8fd9\u4e2a\u7ebf\u7d22\u8981\u548c\u75c7\u72b6\u65f6\u95f4\u5bf9\u8d77\u6765\u770b\u3002"],
                "question": [f"\u8fd9\u4e2a\u8bf4\u6cd5\u5148\u522b\u5413\u5bb6\u957f\u3002\u6211\u4eec\u8981\u95ee\u7684\u662f\uff1a\u8c01\u51fa\u73b0\u75c7\u72b6\uff0c\u4ec0\u4e48\u65f6\u5019\uff0c\u5403\u8fc7\u4ec0\u4e48\u3002"],
                "debunk": [f"\u8fd9\u6761\u4f20\u6cd5\u4f1a\u5e72\u6270\u5c31\u533b\u548c\u8c03\u67e5\uff0c\u6211\u5efa\u8bae\u5148\u505c\u4e0b\uff0c\u7b49\u533b\u5b66\u548c\u98df\u7269\u7ebf\u7d22\u5bf9\u4e0a\u3002"],
            },
            "\u5510\u6653\u8212": {
                "share": [f"\u6211\u5148\u8bb0\u4e0b\u6765\uff1a{memory_hint}\u3002\u7b49\u4e00\u4e0b\u6211\u4eec\u628a\u5b83\u653e\u5230\u201c\u5f85\u6838\u5b9e\u201d\u90a3\u4e00\u680f\u3002"],
                "question": [f"\u8fd9\u4e2a\u6211\u5148\u4e0d\u5f53\u7ed3\u8bba\u5199\u3002\u4f60\u80fd\u5e2e\u6211\u8865\u4e00\u4e0b\uff0c\u662f\u8c01\u8bf4\u7684\u3001\u4ec0\u4e48\u65f6\u5019\u8bf4\u7684\u5417\uff1f"],
                "debunk": [f"\u8fd9\u6761\u6211\u4f1a\u6807\u6ce8\u4e3a\u672a\u6838\u5b9e\u3002\u73b0\u5728\u4e0d\u662f\u538b\u4f4f\u8c01\uff0c\u662f\u522b\u8ba9\u9519\u8bdd\u7ee7\u7eed\u5f80\u5916\u8dd1\u3002"],
            },
        }
        generic = {
            "share": [f"{memory_hint}\u3002{concern}\uff0c\u6240\u4ee5\u6211\u60f3\u5148\u8ddf\u4f60\u5bf9\u4e00\u4e0b\u3002"],
            "question": [f"\u6211\u8fd8\u662f\u60f3\u518d\u6838\u4e00\u4e0b\uff1a{memory_hint}\u3002\u8fd9\u4e2a\u6765\u6e90\u80fd\u786e\u5b9a\u5417\uff1f"],
            "debunk": [f"\u5148\u522b\u628a\u8fd9\u4e2a\u5f53\u7ed3\u8bba\u4f20\u3002{memory_hint}\u8fd8\u9700\u8981\u8bc1\u636e\u3002"],
        }
        options = style_bank.get(name, generic).get(action, generic.get(action, generic["share"]))
        index = self.rng.randrange(len(options))
        line = options[index]
        if previous and line[:16] in previous:
            line = options[(index + 1) % len(options)]
        return line

    def _silent_line(self, source: Agent, target: Agent, concern: str) -> str:
        if source.name in {"\u5218\u5c0f\u654f", "\u5468\u5c0f\u827a", "\u97e9\u5c0f\u96ea"}:
            return f"\u8bdd\u5230\u5634\u8fb9\u505c\u4e86\u4e00\u4e0b\uff1a\u201c\u6211\u5148\u4e0d\u8bf4\u4e86\uff0c\u6211\u6015\u8bf4\u9519\u3002\u201d"
        return f"\u6c89\u9ed8\u4e86\u51e0\u79d2\uff1a\u201c{concern}\u3002\u4f46\u8fd9\u53e5\u8bdd\u6211\u5148\u4e0d\u5f80\u5916\u4f20\u3002\u201d"

    def _generate_reply(self, source: Agent, target: Agent, previous_content: str) -> str:
        llm_line = self._generate_dialogue_with_llm(source, target, "reply")
        if llm_line:
            return llm_line
        concern = self._agent_concern(source)
        relation = source.relations.get(target.id)
        rel_text = relation.relation_type if relation else "\u719f\u4eba"
        prefix = self._dialogue_prefix(source, target, rel_text)
        reply_map = {
            "\u6797\u5c0f\u96e8": [f"\u6211\u77e5\u9053\u4f60\u4eec\u6025\uff0c\u6211\u4e5f\u6025\u3002\u4f46\u73b0\u5728\u5b69\u5b50\u7684\u60c5\u51b5\u3001\u533b\u9662\u7684\u8bdd\u3001\u56ed\u91cc\u7684\u8bb0\u5f55\uff0c\u4e00\u6761\u90fd\u4e0d\u80fd\u4e71\u3002", f"\u4f60\u8fd9\u6837\u95ee\u6211\u4e0d\u8eb2\uff0c\u53ea\u662f\u6709\u4e9b\u4e8b\u6211\u5f97\u5148\u786e\u8ba4\uff0c\u4e0d\u7136\u8bf4\u51fa\u53bb\u53cd\u800c\u5bb3\u4e86\u5927\u5bb6\u3002"],
            "\u5218\u5c0f\u654f": [f"\u6211\u4e0d\u662f\u4e0d\u60f3\u8bf4\u3002\u6211\u662f\u771f\u7684\u6015\u6211\u8bf4\u5b8c\uff0c\u4e8b\u60c5\u5c31\u518d\u4e5f\u6536\u4e0d\u56de\u6765\u4e86\u3002", f"\u5c0f\u96e8\uff0c\u6211\u5fc3\u91cc\u4e00\u76f4\u5361\u7740\u90a3\u5929\u7684\u753b\u9762\uff0c\u4f46\u6211\u73b0\u5728\u8fd8\u6ca1\u6709\u52c7\u6c14\u5f53\u7740\u6240\u6709\u4eba\u8bb2\u3002"],
            "\u9648\u601d\u8fdc": [f"\u6211\u4e0d\u60f3\u628a\u8fd9\u4ef6\u4e8b\u53d8\u6210\u53c8\u4e00\u6b21\u4e92\u76f8\u5b9a\u7f6a\u3002\u6211\u66f4\u60f3\u77e5\u9053\uff0c\u54ea\u4e2a\u73af\u8282\u5f00\u59cb\u628a\u5b69\u5b50\u653e\u5230\u4e86\u540e\u9762\u3002"],
            "\u5f20\u56fd\u5e86": [f"\u6211\u8f66\u4e0a\u8fd9\u51e0\u5929\u542c\u5230\u7684\u7248\u672c\u592a\u591a\u4e86\u3002\u8bf4\u771f\u7684\uff0c\u6211\u73b0\u5728\u8fde\u8bb2\u6545\u4e8b\u90fd\u4e0d\u6562\u6dfb\u6cb9\u4e86\u3002"],
            "\u97e9\u5c0f\u96ea": [f"\u6211\u4e0d\u77e5\u9053\u8be5\u4e0d\u8be5\u8bf4\uff0c\u4f46\u6211\u542c\u5230\u2018\u98df\u5802\u2019\u4e24\u4e2a\u5b57\u7684\u65f6\u5019\uff0c\u8111\u5b50\u91cc\u4e00\u4e0b\u5c31\u60f3\u5230\u4ee5\u524d\u6392\u961f\u5403\u996d\u7684\u6837\u5b50\u3002"],
            "\u5510\u6653\u8212": [f"\u597d\uff0c\u8fd9\u53e5\u6211\u5148\u8bb0\u5230\u2018\u5f85\u6838\u5b9e\u2019\u91cc\u3002\u4f60\u4eec\u5148\u522b\u4e92\u76f8\u9876\uff0c\u6211\u4eec\u628a\u4e8b\u60c5\u4e00\u6761\u6761\u62c6\u5f00\u3002"],
        }
        options = reply_map.get(source.name)
        if options:
            return prefix + options[self.rng.randrange(len(options))]
        if source.skepticism > 0.5:
            return prefix + f"\u6211\u5148\u63a5\u4f4f\u8fd9\u53e5\u8bdd\uff0c\u4f46\u6211\u9700\u8981\u770b\u5230\u6765\u6e90\u3002{concern}\u3002"
        return prefix + f"\u6211\u660e\u767d\u4f60\u7684\u610f\u601d\u3002{concern}\uff0c\u6240\u4ee5\u6211\u4e0d\u60f3\u968f\u4fbf\u628a\u8bdd\u8bf4\u6b7b\u3002"

    def _record_dialogue(self, source, target, action, content):
        row = {"id": str(uuid.uuid4()), "timeStep": self.time_step, "agentId": source.id, "agentName": source.name, "personaType": source.persona_type, "status": STATE_LABELS[source.state], "content": content, "sentiment": "\u4e2d\u6027", "emotionIntensity": round((source.arousal + source.anxiety + source.anger) / 3, 3), "stance": round(source.stance, 3), "osi": round(source.osi, 3), "cpi": round(source.cpi, 3), "actionType": action, "receivers": [target.id], "receiverNames": [target.name], "includedInReport": action != "ignore", "recordType": "dialogue"}
        self.speeches.append(row)
        source.memory.add(self.time_step, "dialogue", content, row["emotionIntensity"], ["event", action, target.name])
        self._write_original_chat_memory(source, target, content, row["emotionIntensity"])
        source_rel = source.relations.get(target.id)
        if source_rel:
            source_rel.interaction_count += 1
            source_rel.last_message = content
        self.pair_cooldown[pair(source.id, target.id)] = self.time_step

    def _receive(self, target, source, action, content):
        target.exposure_count += 1
        if target.state == "UNAWARE":
            target.state = "LISTENING"
        rel = target.relations.get(source.id)
        if rel:
            rel.interaction_count += 1
            rel.last_message = content
            rel.trust_score = self._updated_trust(rel.trust_score, action, target, source)
        delta = 0.04 if action == "share" else 0.01 if action == "reply" else -0.03 if action == "debunk" else -0.015
        target.stance = signed(target.stance + delta * (rel.trust_score if rel else 0.55) * (0.7 + target.osi))
        target.memory.add(self.time_step, "perceived_dialogue", f"\u4ece{source.name}\u542c\u5230\uff1a{content}", 0.6, ["event", source.name])
        self._write_original_event_memory(target, source, content)

    def _updated_trust(self, trust: float, action: str, target: Agent, source: Agent) -> float:
        emotion = (source.arousal + source.anxiety + source.anger) / 3
        if action == "reply":
            delta = 0.015
        elif action == "share":
            delta = 0.018 if source.stance * target.stance >= -0.02 else -0.012
        elif action == "question":
            delta = -0.010 + 0.012 * target.skepticism
        elif action == "debunk":
            delta = 0.020 * target.skepticism - 0.018 * emotion
        else:
            delta = -0.006
        return clamp(trust + delta)

    def _write_original_chat_memory(self, source: Agent, target: Agent, content: str, poignancy: float) -> None:
        if not source.a_mem or not source.scratch:
            return
        created = self._curr_datetime()
        source.scratch.curr_time = created
        chat_rows = [[source.name, self._strip_line_prefix(content, source, target)]]
        try:
            source.a_mem.add_chat(
                created,
                created + datetime.timedelta(days=30),
                source.name,
                "chat with",
                target.name,
                f"{source.name} chatted with {target.name} about the kindergarten food poisoning incident",
                {source.name, target.name, "chat", "food poisoning", "kindergarten"},
                max(1, min(10, int(poignancy * 10))),
                (content, [0.0] * 1536),
                chat_rows,
            )
            source.scratch.chatting_with = target.name
            source.scratch.chat = (source.scratch.chat or []) + chat_rows
            source.scratch.chatting_end_time = created + datetime.timedelta(minutes=5)
            source.scratch.importance_trigger_curr -= max(1, min(10, int(poignancy * 10)))
        except Exception:
            return

    def _write_original_event_memory(self, target: Agent, source: Agent, content: str) -> None:
        if not target.a_mem or not target.scratch:
            return
        created = self._curr_datetime()
        target.scratch.curr_time = created
        desc = f"{target.name} heard from {source.name}: {self._strip_line_prefix(content, source, target)}"
        try:
            target.a_mem.add_event(
                created,
                created + datetime.timedelta(days=30),
                target.name,
                "heard from",
                source.name,
                desc,
                {target.name, source.name, "event", "food poisoning", "kindergarten"},
                6,
                (desc, [0.0] * 1536),
                None,
            )
            target.scratch.importance_trigger_curr -= 6
        except Exception:
            return

    def _strip_line_prefix(self, content: str, source: Agent, target: Agent) -> str:
        for marker in [f"{source.name}\u5bf9{target.name}\u8bf4\uff1a", "\u8bf4\uff1a"]:
            if marker in content:
                return content.split(marker, 1)[-1].strip().strip("\u201c\u201d\"")
        return content

    def _curr_datetime(self) -> datetime.datetime:
        return datetime.datetime(2026, 5, 11, 9, 0, 0) + datetime.timedelta(minutes=self.time_step * 5)

    def _record_reflection(self, source, insight):
        self.speeches.append({"id": str(uuid.uuid4()), "timeStep": self.time_step, "agentId": source.id, "agentName": source.name, "personaType": source.persona_type, "status": STATE_LABELS["REFLECTING"], "content": insight, "sentiment": "\u4e2d\u6027", "emotionIntensity": round((source.arousal + source.anxiety + source.anger) / 3, 3), "stance": round(source.stance, 3), "osi": round(source.osi, 3), "cpi": round(source.cpi, 3), "actionType": "reflect", "receivers": [], "receiverNames": [], "includedInReport": True, "recordType": "reflection"})

    def _conversation_pairs(self):
        candidates = []
        for a, b in self.edges:
            if self.time_step - self.pair_cooldown.get(pair(a, b), -99) <= 2:
                continue
            for source_id, target_id in ((a, b), (b, a)):
                source, target = self.agents[source_id], self.agents[target_id]
                if source.state not in ACTIVE_STATES and target.state == "UNAWARE":
                    continue
                pressure = self._activation_pressure(target)
                target.activation_pressure = pressure
                near_threshold = pressure >= target.activation_threshold * 0.72
                if source.state not in ACTIVE_STATES and not near_threshold:
                    continue
                relation = source.relations.get(target_id)
                trust = relation.trust_score if relation else self.config["default_trust"]
                community_bias = self._community_weight(source, target)
                bridge_bonus = self.config["bridge_bonus"] if source.network_role == "bridge_connector" or target.network_role == "bridge_connector" else 1.0
                recent_need = 1 + min(target.exposure_count, 4) * 0.08
                score = trust * community_bias * bridge_bonus * recent_need
                score += pressure * 0.30 + target.cpi * 0.16 + self.rng.random() * 0.08
                candidates.append((score, source_id, target_id))
        candidates.sort(reverse=True)
        limit = max(1, min(2, len(candidates)))
        pairs = []
        used = set()
        for _, source_id, target_id in candidates:
            if source_id in used or target_id in used:
                continue
            target = self.agents[target_id]
            activation_ratio = target.activation_pressure / max(0.01, target.activation_threshold)
            talk_probability = clamp(0.25 + activation_ratio * 0.42 + target.cpi * 0.18)
            if self.rng.random() < talk_probability:
                pairs.append((source_id, target_id))
                used.update([source_id, target_id])
            if len(pairs) >= limit:
                break
        return pairs

    def _decide(self, source: Agent, target: Agent):
        source.activation_pressure = self._activation_pressure(source)
        rel = source.relations.get(target.id)
        trust = rel.trust_score if rel else self.config["default_trust"]
        memory_pressure = sum(m.poignancy for m in source.memory.retrieve(["event", "rumor", "evidence"], 3)) / 3
        if source.state not in ACTIVE_STATES and source.activation_pressure < source.activation_threshold:
            source.state = "SILENT"
            return "ignore"
        emotion = (source.arousal + source.anxiety + source.anger) / 3
        uncertainty = clamp(1 - source.trust + memory_pressure * 0.2)
        evidence = min(1.0, sum(1 for m in source.memory.retrieve(["evidence", "intervention"], 5) if m.kind in {"intervention", "evidence"}) * 0.35)
        share_score = source.activation_pressure * trust * emotion * (1 - source.skepticism * 0.65)
        question_score = source.activation_pressure * uncertainty * source.skepticism
        debunk_score = (evidence + source.skepticism * 0.45) * source.social_responsibility * (1 - trust * 0.25)
        if debunk_score >= max(share_score, question_score) and debunk_score > 0.18:
            source.state = "DEBUNKING"
            return "debunk"
        if question_score >= share_score and question_score > 0.12:
            source.state = "QUESTIONING"
            return "question"
        source.state = "TALKING"
        return "share"

    def _activation_pressure(self, agent: Agent):
        pressure = 0.0
        for neighbor_id in self.adjacency[agent.id]:
            neighbor = self.agents[neighbor_id]
            if neighbor.state not in ACTIVE_STATES:
                continue
            pressure += self._edge_influence(neighbor, agent)
        return clamp(pressure)

    def _edge_influence(self, source: Agent, target: Agent):
        relation = target.relations.get(source.id) or source.relations.get(target.id)
        trust = relation.trust_score if relation else self.config["default_trust"]
        relation_weight = 0.72 + trust * 0.35
        community_weight = self._community_weight(source, target)
        bridge_bonus = self.config["bridge_bonus"] if source.network_role == "bridge_connector" or target.network_role == "bridge_connector" else 1.0
        emotion = (source.arousal + source.anxiety + source.anger) / 3
        action_weight = {"TALKING": 0.85, "EXPOSED": 0.55, "QUESTIONING": 0.45, "DEBUNKING": -0.35, "REFLECTING": 0.25}.get(source.state, 0.0)
        raw = action_weight * relation_weight * community_weight * bridge_bonus * (0.62 + emotion)
        return max(-0.35, raw)

    def _community_weight(self, source: Agent, target: Agent):
        return self.config["alpha_in"] if source.community == target.community else self.config["alpha_out"]

    def _intervene(self, intervention):
        for aid in intervention.get("target_nodes") or self.report.get("keyNodes", [])[:3]:
            a = self.agents.get(aid)
            if not a:
                continue
            a.state = "DEBUNKING"
            a.memory.add(self.time_step, "intervention", intervention.get("content", "\u8865\u5145\u5b8c\u6574\u65f6\u95f4\u7ebf\u548c\u8bc1\u636e\u3002"), 0.85, ["evidence", "intervention"])


def pair(a: str, b: str) -> Tuple[str, str]:
    return tuple(sorted((a, b)))


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def signed(value: float) -> float:
    return max(-1.0, min(1.0, value))
