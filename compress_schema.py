schema_definition = {
  "Schema": {
    "EntityTypes": {
      "Person": {
        "description": "Individual human entity.",
        "attributes": {
          "Name": "string",
          "Role": "string",
          "Behavior": "string",
          "Emotion": "string",
          "Quantity": "string",
          "Appearance": {
            "Gender": "string",
            "AgeGroup": "string",
            "Clothing": "string",
            "Accessories": "string",
            "Posture": "string",
            "Expression": "string",
            "Hairstyle": "string",
            "SkinColor": "string",
            "Build": "string"
          }
        }
      },

      "Animal": {
        "description": "Non-human living entity.",
        "attributes": {
          "Species": "string",
          "Behavior": "string",
          "Emotion": "string",
          "Quantity": "string",
          "Appearance": {
            "Color": "string",
            "Size": "string"
          }
        }
      },

      "Organization": {
        "description": "Formal or informal institution such as a company, government agency, school, or group.",
        "attributes": {
          "Name": "string",
          "Type": "string",
          "Location": "string",
          "Quantity": "string",
          "Description": "string"
        }
      },

      "Object": {
        "description": "Physical or manufactured items, or something hard to classify, including tools, furniture, or artifacts.",
        "attributes": {
          "Name": "string",
          "Type": "string",
          "Brand": "string",
          "Material": "string",
          "Color": "string",
          "Quantity": "string",
          "Function": "string"
        }
      },

      "Scene": {
        "description": "A spatial or narrative setting providing background context for entities and events.",
        "attributes": {
          "Name": "string",
          "Style": "string",
          "Lighting": "string",
          "Camera": "string",
          "Environment": "string",
          "Time": "string",
          "Weather": "string",
          "Season": "string",
          "Location": "string"
        }
      },

      "VisualContent": {
        "description": "Digital or screen-based visual elements such as charts, screenshots, or displays.",
        "attributes": {
          "Type": "string",
          "Style": "string",
          "Lighting": "string",
          "Description": "string"
        }
      },

      "Term": {
        "description": "Specialized domain-specific term, concept, or label.",
        "attributes": {
          "Name": "string",
          "Domain": "string",
          "Definition": "string"
        }
      },

      "Event": {
        "description": "Temporal occurrence involving participants, actions, or changes in state.",
        "attributes": {
          "Name": "string",
          "Type": "string",
          "Time": "string",
          "Location": "string",
          "Environment": "string",
          "Participants": "string",
          "Description": "string"
        }
      },

      "Action": {
        "description": "A physical or verbal activity performed by an agent (person, animal, or object).",
        "attributes": {
          "Name": "string",
          "Type": "string",
          "Verb": "string",
          "Duration": "string",
          "Intensity": "string",
          "Direction": "string",
          "Target": "string",
          "Description": "string"
        }
      },

      "Speech": {
        "description": "Spoken utterance or dialogue produced by a person or voice actor.",
        "attributes": {
          "Content": "string",
          "Language": "string",
          "Tone": "string",
          "Emotion": "string",
          "Speaker": "string",
          "Timestamp": "string"
        }
      },

      "Audio": {
        "description": "Non-speech sound elements such as music, ambient noise, or effects.",
        "attributes": {
          "Type": "string",
          "Source": "string",
          "Duration": "string",
          "Volume": "string",
          "Emotion": "string",
          "Timestamp": "string"
        }
      },

      "Sound": {
        "description": "Auditory event representing a sound occurring in the environment.",
        "attributes": {
          "Type": "string",
          "Source": "string",
          "Loudness": "string",
          "Pitch": "string",
          "Duration": "string"
        }
      },

      "Emotion": {
        "description": "An emotional state or affective expression experienced or displayed by an entity.",
        "attributes": {
          "Name": "string",
          "Intensity": "string",
          "Cause": "string",
          "Target": "string"
        }
      },

      "Subtitle": {
        "description": "Text overlay describing spoken content, sounds, or actions in a scene.",
        "attributes": {
          "Content": "string",
          "Language": "string",
          "Style": "string",
          "Timing": "string"
        }
      },

      "Topic": {
        "description": "Thematic or conceptual focus describing a scene, dialogue, or content.",
        "attributes": {
          "Name": "string",
          "Domain": "string",
          "Keywords": "string"
        }
      },

      "Concept": {
        "description": "Abstract conceptual element such as a theory, idea, or mechanism.",
        "attributes": {
          "Name": "string",
          "Definition": "string",
          "Domain": "string"
        }
      },

      "Shot": {
        "description": "A continuous sequence of visual frames forming a unit within a scene.",
        "attributes": {
          "ID": "string",
          "StartTime": "string",
          "EndTime": "string",
          "Camera": "string",
          "Duration": "string",
          "Description": "string"
        }
      }
    },

    "RelationTypes": {
      "Structural": [
        "IsA",
        "PartOf",
        "Has"
      ],

      "Semantic": [
        "RelatedTo",
        "BasedOn",
        "CausedBy"
      ],

      "Spatiotemporal": [
        "LocatedAt",
        "OccursIn",
        "Under",
        "OccursAt"
      ],

      "Actional": [
        "InteractWith",
        "Performs",
        "Uses",
        "Watching",
        "Addressing",
        "Involves"
      ],

      "Communicative": [
        "SpokenBy",
        "Expresses",
        "Describes",
        "AssociatedWith"
      ],

      "Contextual": [
        "LocatedIn",
        "PartOf",
        "UsedIn",
        "OccursIn"
      ],

      "Social": [
        "WorksFor",
        "Founded",
        "MemberOf",
        "LocatedIn"
      ],

      "Conceptual": [
        "RelatedTo",
        "Describes",
        "BasedOn"
      ],

      "Causal": [
        "Performs",
        "Involves",
        "OccursIn",
        "OccursAt",
        "CausedBy"
      ],

      "Perceptual": [
        "DepictedOn",
        "ShownIn",
        "IndicatesSeason"
      ],

      "OtherActions": [
        {
          "description": "Dynamic category allowing extraction of domain-specific or rare actions not covered by other relation types. Examples: 'declined', 'invited', 'resigned', 'proposed', 'approved', 'denied'.",
          "format": ["Subject", "ActionVerb", "Object"],
          "notes": "This relation group is extensible; verbs are captured directly from text, normalized to lowercase infinitives."
        }
      ]
    },

    "DataFormat": {
      "Triples": [
        ["Subject", "Relation", "Object"]
      ],
      "Entity types": {
        "EntityName": "EntityType"
      },
      "Attributes": {
        "EntityName": {
          "AttributeName": "AttributeValue"
        }
      }
    },

    "Notes": {
      "1": "Entities represent multimodal components — visual, auditory, textual, and conceptual.",
      "2": "Triples express semantic, causal, spatial, and communicative relationships among entities.",
      "3": "Attributes describe internal or visual properties of entities.",
      "4": "Appearance remains a nested structure to represent complex perceptual traits.",
      "5": "Supports multimodal parsing from video, subtitles, and audio transcripts.",
      "6": "Extensible for domain-specific relations through OtherActions verbs."
    }
  }
}
import string

def build_schema_maps(schema_json, start_entity_code='A', start_attr_code='a', start_rel_code='r'):
    """
    从Schema自动生成实体类型、属性和关系缩写映射表。
    支持嵌套属性（使用点号展开）。

    Args:
        schema_json (dict): 你的Schema JSON对象
        start_entity_code (str): 实体类型起始字母（默认 'A'）
        start_attr_code (str): 属性起始字母（默认 'a'）
        start_rel_code (str): 关系起始字母（默认 'r'）

    Returns:
        dict: { "entity_map": {...}, "attr_map": {...}, "relation_map": {...} }
    """
    entity_map = {}
    attr_map = {}
    relation_map = {}

    # =============================
    # 1️⃣ 实体类型映射
    # =============================
    entity_types = list(schema_json["Schema"]["EntityTypes"].keys())
    for i, etype in enumerate(entity_types):
        code = chr(ord(start_entity_code) + i)
        entity_map[etype] = code

    # =============================
    # 2️⃣ 属性映射（包括嵌套）
    # =============================
    all_attrs = []
    for etype, detail in schema_json["Schema"]["EntityTypes"].items():
        attrs = detail.get("attributes", {})
        for attr_name, attr_val in attrs.items():
            if isinstance(attr_val, dict):  # 嵌套结构，如 Appearance
                for sub_key in attr_val.keys():
                    all_attrs.append(f"{attr_name}.{sub_key}")
            else:
                all_attrs.append(attr_name)

    # 去重
    all_attrs = sorted(set(all_attrs))

    # 分配简写（前缀 a, b, c...，若超26个则 aa, ab, ac...）
    def gen_codes(prefix, items):
        letters = list(string.ascii_lowercase)
        codes = []
        for i in range(len(items)):
            if i < 26:
                codes.append(letters[i])
            else:
                # 超过26个时两位组合 aa, ab...
                codes.append(letters[i // 26 - 1] + letters[i % 26])
        return codes

    attr_codes = gen_codes('a', all_attrs)
    for attr_name, code in zip(all_attrs, attr_codes):
        attr_map[attr_name] = code

    # =============================
    # 3️⃣ 关系映射
    # =============================
    relation_groups = schema_json["Schema"]["RelationTypes"]
    all_rels = []
    for group, rel_list in relation_groups.items():
        if isinstance(rel_list, list):
            for rel in rel_list:
                if isinstance(rel, str):
                    all_rels.append(rel)
        elif isinstance(rel_list, dict):
            # 兼容 OtherActions 结构
            all_rels.extend(rel_list.get("format", []))
        elif isinstance(rel_list, list) and len(rel_list) and isinstance(rel_list[0], dict):
            for rel in rel_list:
                all_rels.extend(rel.get("format", []))
    all_rels = sorted(set(all_rels))

    rel_codes = gen_codes(start_rel_code, all_rels)
    for rel, code in zip(all_rels, rel_codes):
        relation_map[rel] = code

    # =============================
    # ✅ 汇总输出
    # =============================
    return {
        "entity_map": entity_map,
        "attr_map": attr_map,
        "relation_map": relation_map
    }

import json
import string
import re


# ==================================================
# 1️⃣ 从 Schema 自动生成映射表
# ==================================================
def build_schema_maps(schema_json, start_entity_code='A', start_attr_code='a', start_rel_code='r'):
    """从Schema自动生成实体类型、属性和关系缩写映射表"""
    entity_map = {}
    attr_map = {}
    relation_map = {}

    # === 实体类型映射 ===
    entity_types = list(schema_json["Schema"]["EntityTypes"].keys())
    for i, etype in enumerate(entity_types):
        code = chr(ord(start_entity_code) + i)
        entity_map[etype] = code

    # === 属性映射 ===
    all_attrs = []
    for etype, detail in schema_json["Schema"]["EntityTypes"].items():
        attrs = detail.get("attributes", {})
        for attr_name, attr_val in attrs.items():
            if isinstance(attr_val, dict):  # 嵌套结构
                for sub_key in attr_val.keys():
                    all_attrs.append(f"{attr_name}.{sub_key}")
            else:
                all_attrs.append(attr_name)

    all_attrs = sorted(set(all_attrs))

    def gen_codes(items):
        letters = list(string.ascii_lowercase)
        codes = []
        for i in range(len(items)):
            if i < 26:
                codes.append(letters[i])
            else:
                codes.append(letters[i // 26 - 1] + letters[i % 26])
        return codes

    attr_codes = gen_codes(all_attrs)
    for attr_name, code in zip(all_attrs, attr_codes):
        attr_map[attr_name] = code

    # === 关系映射 ===
    relation_groups = schema_json["Schema"]["RelationTypes"]
    all_rels = []
    for group, rel_list in relation_groups.items():
        if isinstance(rel_list, list):
            for rel in rel_list:
                if isinstance(rel, str):
                    all_rels.append(rel)
        elif isinstance(rel_list, list) and len(rel_list) and isinstance(rel_list[0], dict):
            for rel in rel_list:
                all_rels.extend(rel.get("format", []))
    all_rels = sorted(set(all_rels))
    rel_codes = gen_codes(all_rels)
    for rel, code in zip(all_rels, rel_codes):
        relation_map[rel] = code

    return {"entity_map": entity_map, "attr_map": attr_map, "relation_map": relation_map}


# ==================================================
# 2️⃣ JSON → Schema-aware Turtle (STTL)
# ==================================================
def simplify_name(name):
    return re.sub(r"[^A-Za-z0-9_]+", "_", name.strip())


def flatten_dict(d, prefix=""):
    flat = {}
    for k, v in d.items():
        if isinstance(v, dict):
            flat.update(flatten_dict(v, f"{prefix}{k}."))
        else:
            flat[f"{prefix}{k}"] = v
    return flat


def convert_json_2_sttl(kg, schema_json, calc_ratio=False):
    """
    压缩知识图谱为 Schema-Aware Turtle (STTL)
    - 用 Schema 缩写实体类型、属性名和关系名
    """
    maps = build_schema_maps(schema_json)
    Emap, Amap, Rmap = maps["entity_map"], maps["attr_map"], maps["relation_map"]

    lines = []
    ent_types = kg.get("Entity_types", {})
    attrs = kg.get("Attributes", {})
    triples = kg.get("Triples", [])

    # === 实体与属性 ===
    for ent, typ in ent_types.items():
        typ_code = Emap.get(typ, "_")
        eid = simplify_name(ent)

        flat_attrs = flatten_dict(attrs.get(ent, {}))
        attr_strs = []
        for k, v in flat_attrs.items():
            if k not in Amap:  # 超出schema的属性舍弃
                continue
            a_code = Amap[k]
            attr_strs.append(f"{a_code}={v}")
        joined = ";".join(attr_strs)
        lines.append(f"{eid}:{typ_code}" + (f"|{joined}" if joined else ""))

    # === 关系 ===
    if triples:
        lines.append("#R")
        for s, r, o in triples:
            s_id, o_id = simplify_name(s), simplify_name(o)
            r_code = Rmap.get(r, r[0].lower())
            lines.append(f"{s_id} {r_code} {o_id}")

    sttl_str = "\n".join(lines)

    if not calc_ratio:
        return sttl_str

    json_len = len(json.dumps(kg, separators=(",", ":")))
    sttl_len = len(sttl_str)
    ratio = sttl_len / json_len if json_len else 0
    return sttl_str, {
        "json_length": json_len,
        "sttl_length": sttl_len,
        "compression_ratio": round(ratio, 3),
        "reduction_percent": round((1 - ratio) * 100, 1)
    }


# ==================================================
# 3️⃣ STTL → JSON
# ==================================================
def convert_sttl_2_json(sttl_text, schema_json):
    """从 STTL 反解析回标准 JSON"""
    maps = build_schema_maps(schema_json)
    Emap, Amap, Rmap = maps["entity_map"], maps["attr_map"], maps["relation_map"]
    rev_E = {v: k for k, v in Emap.items()}
    rev_A = {v: k for k, v in Amap.items()}
    rev_R = {v: k for k, v in Rmap.items()}

    kg = {"Triples": [], "Entity_types": {}, "Attributes": {}}

    lines = [l.strip() for l in sttl_text.splitlines() if l.strip()]
    mode = "entity"

    for line in lines:
        if line.startswith("#R"):
            mode = "rel"
            continue

        if mode == "entity":
            if ":" not in line:
                continue
            ent_part, rest = line.split(":", 1)
            ent_name = ent_part.replace("_", " ").strip()
            if "|" in rest:
                type_code, attr_part = rest.split("|", 1)
            else:
                type_code, attr_part = rest, ""
            ent_type = rev_E.get(type_code.strip(), "Unknown")

            attrs = {}
            if attr_part:
                for pair in attr_part.split(";"):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        key_name = rev_A.get(k.strip(), None)
                        if key_name:
                            attrs[key_name] = v.strip()
            kg["Entity_types"][ent_name] = ent_type
            kg["Attributes"][ent_name] = attrs

        elif mode == "rel":
            if not line or len(line.split()) < 3:
                continue
            s, r, o = line.split(maxsplit=2)
            rel = rev_R.get(r, r)
            kg["Triples"].append([s.replace("_", " "), rel, o.replace("_", " ")])

    return kg

if __name__ == "__main__":
    schema_maps = build_schema_maps(schema_definition)
    print(schema_maps)

    # === 模拟一个小型KG ===
    kg = {
        "Triples": [
            ["Leonardo DiCaprio", "Performs", "talking about winning awards"],
            ["Leonardo DiCaprio", "Expresses", "winning awards"]
        ],
        "Entity_types": {
            "Leonardo DiCaprio": "Person",
            "talking about winning awards": "Action",
            "winning awards": "Event"
        },
        "Attributes": {
            "Leonardo DiCaprio": {
                "Name": "Leonardo DiCaprio",
                "Role": "actor",
                "Behavior": "talking"
            },
            "talking about winning awards": {
                "Name": "talking about winning awards",
                "Type": "verbal communication",
                "Verb": "talking",
                "Target": "winning awards",
                "Description": "discussing award victories"
            },
            "winning awards": {
                "Name": "winning awards",
                "Type": "achievement event",
                "Participants": "Leonardo DiCaprio",
                "Description": "recognition of excellence through awards"
            }
        }
    }

    # === 压缩为 STTL ===
    from pprint import pprint
    sttl, stats = convert_json_2_sttl(kg, schema_definition, calc_ratio=True)
    print("=== STTL ===")
    print(sttl)
    print("\n=== Compression Stats ===")
    pprint(stats)

    # === 还原为 JSON ===
    restored = convert_sttl_2_json(sttl, schema_definition)
    print("\n=== Restored JSON ===")
    print(json.dumps(restored, indent=2, ensure_ascii=False))
