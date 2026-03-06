# parse the .ump files to extract a similar structure to the metrics object in main 

import re
import sys

umple_code = """
[paste your umple code here, or read from file]
"""

# ── helpers ──────────────────────────────────────────────────────────────────

def extract_classes(code):
    """Return a dict  { ClassName: raw_body_string }"""
    classes = {}
    pattern = re.compile(r'\bclass\s+(\w+)\s*\{', re.MULTILINE)
    for m in pattern.finditer(code):
        name  = m.group(1)
        start = m.end()          # position just after the opening {
        depth = 1
        i     = start
        while i < len(code) and depth:
            if   code[i] == '{': depth += 1
            elif code[i] == '}': depth -= 1
            i += 1
        classes[name] = code[start:i-1]
    return classes


def strip_comments(text):
    """Remove // … comments."""
    return re.sub(r'//[^\n]*', '', text)


def extract_attributes(body):
    """
    Return a list of plain attribute names / typed attributes found in the body.
    Ignores association lines, isA, abstract, enum blocks, depend, and raw Java.
    """
    body = strip_comments(body)

    # remove enum blocks entirely
    body = re.sub(r'\benum\s+\w+\s*\{[^}]*\}', '', body, flags=re.DOTALL)

    # remove Java method bodies  { … }
    body = re.sub(r'\{[^{}]*\}', '', body, flags=re.DOTALL)

    attrs = []
    # tokens that signal a non-attribute line
    skip_prefixes = re.compile(
        r'^\s*('
        r'\d|'                      # associations start with multiplicity digits
        r'isA|abstract|depend|'
        r'private|public|protected|static|void|'
        r'Boolean\s+\w+\s*;'        # handled below as typed attr
        r')', re.IGNORECASE)

    typed_attr   = re.compile(r'^\s*(int|Boolean|Date|Time|String)\s+(\w+)\s*;')
    simple_attr  = re.compile(r'^\s*(?:unique\s+)?(\w+)\s*;')
    assoc_line   = re.compile(r'[-<>@*]')  # association punctuation

    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue

        # typed attribute  e.g.  int duration;  Boolean mandatory;
        m = typed_attr.match(line)
        if m:
            attrs.append(f"{m.group(2)} : {m.group(1)}")
            continue

        # skip lines with association symbols or known keywords
        if assoc_line.search(line):
            continue
        if re.match(r'isA|abstract|depend|enum|private|public|protected|'
                    r'static|void|return|String\[|if\(|sysDate|sysTime', line, re.I):
            continue

        # plain / unique attribute  e.g.  username;   unique name;
        m = simple_attr.match(line)
        if m:
            attrs.append(f"{m.group(1)}")

    return attrs


# ── association kinds ────────────────────────────────────────────────────────

ASSOC_PATTERNS = [
    # composition  <@>-
    (re.compile(
        r'(\S+)\s+<@>-\s+(\S+)\s+(\w+)\s*;?'),                 'composition (<@>-)'),
    # bidirectional  --
    (re.compile(
        r'(\S+)\s+--\s+(\S+)\s+(\w+)\s*;?'),                   'bidirectional (--)'),
    # directed  ->
    (re.compile(
        r'(\S+)\s+->\s+(\S+)\s+(\w+)\s*;?'),                   'directed (->)'),
]


def extract_associations(classes_bodies):
    """Return list of dicts describing each association."""
    results = []
    for class_name, body in classes_bodies.items():
        body_clean = strip_comments(body)
        for line in body_clean.splitlines():
            line = line.strip()
            for pattern, kind in ASSOC_PATTERNS:
                m = pattern.search(line)
                if m:
                    results.append({
                        'from'        : class_name,
                        'from_mult'   : m.group(1),
                        'kind'        : kind,
                        'to_mult'     : m.group(2),
                        'to_role'     : m.group(3),
                        'raw'         : line,
                    })
                    break   # one match per line is enough
    return results


# ── main ─────────────────────────────────────────────────────────────────────

def parse_umple_code(umple_code):
    """
    Parse umple code string and return classes and associations.
    
    Args:
        umple_code: String containing umple code
    
    Returns:
        Dict with 'classes' and 'associations'
    """
    classes = extract_classes(umple_code)

    # ── classes & attributes ─────────────────────────────────────────────────
    classes_json = {}
    for cls, body in classes.items():
        attrs = extract_attributes(body)
        inh = re.search(r'\bisA\s+(\w+)', body)
        classes_json[cls] = {
            "extends": inh.group(1) if inh else None,
            "attributes": attrs
        }

    # ── associations ─────────────────────────────────────────────────────────
    associations_json = {}
    for a in extract_associations(classes):
        src = a["from"]
        if src not in associations_json:
            associations_json[src] = []
        associations_json[src].append({
            "to": a["to_role"],
            "from_multiplicity": a["from_mult"],
            "to_multiplicity": a["to_mult"],
            "kind": a["kind"]
        })

    result = {
        "classes": classes_json,
        "associations": associations_json
    }

    return result


def main(umple_file_or_code):
    """
    Parse umple file or code string and return classes and associations.
    
    Args:
        umple_file_or_code: Either a file path to a .ump file, or umple code string
    
    Returns:
        Dict with 'classes' and 'associations'
    """
    import os
    
    # Check if it's a file path
    if isinstance(umple_file_or_code, str) and (
        umple_file_or_code.endswith('.ump') or os.path.isfile(umple_file_or_code)
    ):
        print(f"Reading umple file: {umple_file_or_code}")
        with open(umple_file_or_code, encoding="utf-8") as f:
            umple_code = f.read()
        print(f"File read successfully ({len(umple_code)} characters)")
    else:
        # Assume it's raw umple code
        umple_code = umple_file_or_code
        print(f"Parsing umple code ({len(umple_code)} characters)")
    
    result = parse_umple_code(umple_code)
    
    print(f"Parsed {len(result['classes'])} classes")
    for cls_name in result['classes']:
        print(f"  - {cls_name}: {len(result['classes'][cls_name]['attributes'])} attributes")

    return result


if __name__ == "__main__":
    # Test with a file path
    path = "/u/mancasat/Desktop/summer_intern/domain-concepts-identification-using-LLMs-aless/data_mcgill/F20_G3/FlexiBook.ump"
    result = main(path)
    
    # Or you can pass raw umple code:
    # umple_code = """
    # class Example {
    #   name;
    # }
    # """
    # result = main(umple_code)
