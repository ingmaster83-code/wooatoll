# -*- coding: utf-8 -*-
"""
data/toll_raw.csv (한국도로공사_통행요금조회, data.go.kr id 15043728, CP949 CSV)
-> data/toll.json (페이지 생성용)

컬럼: 출발요금소/도착요금소/1종~6종 요금(원). 좌표·지오코딩 불필요(장소검색이 아니라
두 지점간 요금 조회형 콘텐츠). 231,884개 방향쌍(608개 요금소), 자기자신 쌍(373건) 제외.

사용법: python scripts/parse_toll.py
"""
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
RAW_CSV = ROOT / "data" / "toll_raw.csv"
OUT = ROOT / "data" / "toll.json"
GATES_OUT = ROOT / "data" / "gates.json"

VCLASS_LABEL = {
    1: "1종(승용차)", 2: "2종(중형차)", 3: "3종(대형차)",
    4: "4종(대형화물)", 5: "5종(대형화물)", 6: "6종(경차)",
}


def slugify(name):
    base = re.sub(r"[^\w가-힣]", "", name) or "gate"
    h = hashlib.md5(name.encode("utf-8")).hexdigest()[:6]
    return f"{base}-{h}"


def main():
    rows = list(csv.reader(RAW_CSV.read_text(encoding="cp949", errors="replace").splitlines()))
    header, data_rows = rows[0], rows[1:]
    print("header:", header)

    out = []
    skipped = 0
    for r in data_rows:
        if len(r) != 8:
            skipped += 1
            continue
        dep, arr = r[0].strip(), r[1].strip()
        if not dep or not arr or dep == arr:
            skipped += 1
            continue
        try:
            charges = [int(x.strip()) for x in r[2:8]]
        except ValueError:
            skipped += 1
            continue
        out.append({
            "dep": dep, "arr": arr,
            "depSlug": slugify(dep), "arrSlug": slugify(arr),
            "charges": charges,  # [1종,2종,3종,4종,5종,6종] 순서
        })

    # 요금소별 목적지 개수 집계(허브페이지·소개문장용)
    dep_count = Counter(o["dep"] for o in out)

    for o in out:
        o["depDestCount"] = dep_count[o["dep"]]

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    gates = sorted({(o["dep"], o["depSlug"]) for o in out} | {(o["arr"], o["arrSlug"]) for o in out})
    GATES_OUT.write_text(
        json.dumps([{"name": n, "slug": s} for n, s in gates], ensure_ascii=False, indent=1),
        encoding="utf-8",
    )

    print(f"총 {len(data_rows)}건 중 {len(out)}개 저장, {skipped}개 스킵 -> {OUT}")
    print(f"요금소 {len(gates)}개 -> {GATES_OUT}")


if __name__ == "__main__":
    main()
