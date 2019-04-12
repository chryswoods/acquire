
import pytest

from Acquire.Identity import ACLRule, ACLRules, ACLGroupRules, ACLUserRules


def test_acls():
    rule = ACLRule.inherit()
    assert(rule.inherits_all())
    assert(rule.inherits_owner())
    assert(rule.inherits_readable())
    assert(rule.inherits_writeable())
    assert(rule.inherits_executable())

    upstream = ACLRule.writer()

    resolved = rule.resolve(upstream=upstream)

    assert(resolved == upstream)

    rules = ACLRules()
    assert(rules.is_simple_inherit())

    rule = rules.resolve(must_resolve=False)
    assert(rule.inherits_all())

    rule = rules.resolve()
    assert(rule.denied_all())

    data = rules.to_data()
    assert(data == "inherit")

    rules = ACLRules.from_data(data)
    assert(rules.is_simple_inherit())

    user_guid = "someone@somewhere"
    identifiers = {"user_guid": user_guid}

    user_guid2 = "someone_else@somewhere"
    identifiers2 = {"user_guid": user_guid2}

    rule = rules.resolve(identifiers=identifiers, must_resolve=False)
    assert(rule.inherits_all())

    rule = rules.resolve(identifiers=identifiers2, must_resolve=True)
    assert(rule.denied_all())

    user_rule = ACLUserRules.owner(user_guid=user_guid)
    assert(user_rule.resolve(identifiers=identifiers).is_owner())

    rules = ACLRules(rule=user_rule, default_rule=ACLRule.denied())
    assert(rules.resolve(identifiers=identifiers).is_owner())
    assert(rules.resolve(identifiers=identifiers2).denied_all())

    data = rules.to_data()

    rules = ACLRules.from_data(data)

    assert(rules.resolve(identifiers=identifiers).is_owner())
    assert(rules.resolve(identifiers=identifiers2).denied_all())

    data = ACLRules.inherit().to_data()
    assert(ACLRules.from_data(data).is_simple_inherit())
