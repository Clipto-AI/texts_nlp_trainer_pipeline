import re
import json
from typing import Dict

schema_maps = "/Users/universe/Desktop/complate_format/schema_maps.json"
with open(schema_maps,"r",encoding="utf-8") as f:
    maps = json.load(f)


def connect_entity(entity_str: str) -> str:
    return re.sub(r'[^A-Za-z0-9_]+', "_", entity_str.strip())

def flatten_dict(d: dict, prefix: str = "") -> dict:
    flat = {}
    for k, v in d.items():
        if isinstance(v, dict):
            flat.update(flatten_dict(v, f"{prefix}{k}."))
        else:
            flat[f"{prefix}{k}"] = v
    return flat

def jsonTosttl(kg: dict, maps: dict, include_mentions: bool = True) -> str:
    """
    生成 STTL 格式：
    - 每个实体一行 entity_id:typ_code|a=b;...
    - 如果 include_mentions=True，则把 Entity mentions 写入 m=
    """
    lines = []
    Emap, Amap, Rmap = maps["entity_map"], maps["attr_map"], maps["relation_map"]

    Triples = kg.get("Triples", [])
    Entity_types = kg.get("Entity types", {})
    Attributes = kg.get("Attributes", {})
    entity_mentions = kg.get("Entity mentions", {}) if include_mentions else {}

    # ---- 实体部分 ----
    for entity, types in Entity_types.items():
        attr_strs = []
        typ_code = Emap.get(types, "_")
        entity_id = connect_entity(entity)
        flat_attrs = flatten_dict(Attributes.get(entity, {}))

        for k, v in flat_attrs.items():
            if k not in Amap:
                continue
            a_code = Amap[k]
            # 避免分号和双竖干扰结构
            safe_val = str(v).replace(";", "；").replace("||", "|")
            attr_strs.append(f"{a_code}={safe_val}")

        # ---- 是否写入 mentions ----
        if include_mentions and entity in entity_mentions:
            mentions = "||".join(str(m).replace(";", "；") for m in entity_mentions[entity])
            if mentions:
                attr_strs.append(f"m={mentions}")

        joined = ";".join(attr_strs)
        lines.append(f"{entity_id}:{typ_code}" + (f"|{joined}" if joined else ""))

    # ---- 三元组部分 ----
    if Triples:
        lines.append("#R")
        for s, r, o in Triples:
            s_id, o_id = connect_entity(s), connect_entity(o)
            r_code = Rmap.get(r, r[0].lower() if r else r)
            lines.append(f"{s_id} {r_code} {o_id}")

    return "\n".join(lines)


def sttl_to_kg(sttl_str: str, maps: dict, entity_name_map: dict = None, include_mentions: bool = True) -> dict:
    """
    解析端：
    - 解析 m= 部分直接恢复到实体的属性部分
    """
    Emap, Amap, Rmap = maps["entity_map"], maps["attr_map"], maps["relation_map"]
    rev_e = {v: k for k, v in Emap.items()}
    rev_a = {v: k for k, v in Amap.items()}
    rev_r = {v: k for k, v in Rmap.items()}

    kg = {
        "Entity types": {},
        "Attributes": {},
        "Triples": [],
    }

    # 如果 include_mentions 为 True，才处理 Entity mentions 部分
    if include_mentions:
        kg["Entity mentions"] = {}

    lines = sttl_str.strip().splitlines()
    parsing_triples = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if line == "#R":
            parsing_triples = True
            continue

        # 解析三元组
        if parsing_triples:
            parts = line.split()
            if len(parts) == 3:
                s, r_code, o = parts
                rel_name = rev_r.get(r_code, r_code)
                if entity_name_map:
                    s_name = entity_name_map.get(s, s.replace("_", " "))
                    o_name = entity_name_map.get(o, o.replace("_", " "))
                else:
                    s_name, o_name = s.replace("_", " "), o.replace("_", " ")
                kg["Triples"].append([s_name, rel_name, o_name])
            continue

        # 解析实体行（entity:typ|attr;attr;...）
        if ":" in line:
            entity_part, *attr_part = line.split("|", 1)
            entity_id, typ_code = entity_part.split(":", 1)
            entity_type = rev_e.get(typ_code, typ_code)
            if entity_name_map:
                entity_id_clean = entity_name_map.get(entity_id, entity_id.replace("_", " "))
            else:
                entity_id_clean = entity_id.replace("_", " ")
            kg["Entity types"][entity_id_clean] = entity_type

            attrs = {}
            if attr_part:
                attr_block = attr_part[0]
                # 提取 key=value 对
                for m in re.finditer(r'([^\=;]+)=([^;]*)', attr_block):
                    a_code = m.group(1).strip()
                    val = m.group(2).strip()
                    if not a_code:
                        continue
                    if a_code == "m" and include_mentions:
                        mentions_list = [v.strip() for v in val.split("||") if v.strip()]
                        kg["Entity mentions"][entity_id_clean] = mentions_list
                        continue
                    attr_name = rev_a.get(a_code, a_code)
                    attrs[attr_name] = val

                # 恢复嵌套属性 a.b.c 恢复成嵌套字典
                d = {}
                for k, v in attrs.items():
                    keys = k.split(".")
                    temp = d
                    for key in keys[:-1]:
                        temp = temp.setdefault(key, {})
                    temp[keys[-1]] = v
                attrs = d
            kg["Attributes"][entity_id_clean] = attrs

    return kg


if __name__=="__main__":
    kg = {
            "Triples": [
                ["two individuals", "InteractWith", "each other's hands"],
                ["two individuals", "LocatedAt", "outdoor location"],
                ["outdoor location", "RelatedTo", "history or culture"],
                ["a woman", "InteractWith", "a moving train carriage"],
                ["a moving train carriage", "LocatedAt", "train station platform 13"],
                ["train station platform 13", "OccursIn", "daytime"],
                ["setting", "RelatedTo", "indoor public transportation theme"],
                ["a person", "LocatedAt", "room with traditional furniture and decor"],
                ["room with traditional furniture and decor", "RelatedTo", "indoor environment designed for cultural purposes"]
            ],
            "Entity types": {
            "two individuals": "Person",
            "each other's hands": "Object",
            "outdoor location": "Scene",
            "a woman": "Person",
            "a moving train carriage": "Object",
            "train station platform 13": "Scene",
            "setting": "Scene",
            "a person": "Person",
            "room with traditional furniture and decor": "Scene"
        },
         "Attributes": {
            "two individuals": {
            "Quantity": "two",
            "Appearance": {
                "Clothing": "historical-style costumes",
                "Posture": "seated"
            },
            "Behavior": "interacting with hands"
            },
            "each other's hands": {
            "Type": "body part"
            },
            "outdoor location": {
            "Environment": "historical or cultural setting",
            "Lighting": "natural light (outdoor)"
            },
            "a woman": {
            "Appearance": {
                "Gender": "female"
            },
            "Behavior": "walking towards train carriage"
            },
            "a moving train carriage": {
            "Type": "vehicle",
            "Function": "transportation",
            "Behavior": "moving"
            },
            "train station platform 13": {
            "Environment": "public transportation area",
            "Lighting": "daytime natural light"
            },
            "setting": {
            "Environment": "indoor public transportation theme",
            "Weather": "none visible",
            "Season": "unclear"
            },
            "a person": {
            "Behavior": "sitting and looking off-screen",
            "Appearance": {
                "Posture": "sitting"
            }
            },
            "room with traditional furniture and decor": {
            "Environment": "indoor",
            "Style": "traditional cultural aesthetic",
            "Lighting": "indoor lighting",
            "Weather": "not visible"
            }
        },
        "Entity mentions": {
            "two individuals": [
            "two individuals dressed in historical-style costumes",
            "individuals"
            ],
            "each other's hands": [
            "each other's hands"
            ],
            "outdoor location": [
            "outdoor location likely associated with history or culture"
            ],
            "a woman": [
            "a woman"
            ],
            "a moving train carriage": [
            "a moving train carriage"
            ],
            "train station platform 13": [
            "train station platform 13"
            ],
            "setting": [
            "the setting",
            "the setting has an indoor public transportation theme"
            ],
            "a person": [
            "a person sitting in a room"
            ],
            "room with traditional furniture and decor": [
            "room with traditional furniture and dcor"
            ]
        }
    }
    results = jsonTosttl(kg, maps,include_mentions=False)
    print(results)

    # Parse back the STTL
    src = sttl_to_kg(results, maps, include_mentions=False)
    print(json.dumps(src, ensure_ascii=False, indent=2))
        