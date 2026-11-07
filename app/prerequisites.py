import re

class PrerequisiteError(ValueError): pass

def evaluate(expression: str, completed: set[str]) -> bool:
    """Recursive descent grammar. AND binds tighter than OR; no eval/exec."""
    if not expression.strip(): return True
    parts=re.findall(r"\d+|AND|OR|[()]",expression)
    if "".join(parts) != re.sub(r"\s+","",expression): raise PrerequisiteError("Unsupported prerequisite expression")
    pos=0
    def atom():
        nonlocal pos
        if pos>=len(parts): raise PrerequisiteError("Missing operand")
        t=parts[pos];pos+=1
        if t=="(":
            value=disjunction()
            if pos>=len(parts) or parts[pos]!=")": raise PrerequisiteError("Unclosed parenthesis")
            pos+=1;return value
        if t.isdigit(): return t in completed
        raise PrerequisiteError("Invalid operand")
    def conjunction():
        nonlocal pos
        value=atom()
        while pos<len(parts) and parts[pos]=="AND":
            pos+=1;right=atom();value=value and right
        return value
    def disjunction():
        nonlocal pos
        value=conjunction()
        while pos<len(parts) and parts[pos]=="OR":
            pos+=1;right=conjunction();value=value or right
        return value
    value=disjunction()
    if pos!=len(parts): raise PrerequisiteError("Trailing tokens")
    return value
