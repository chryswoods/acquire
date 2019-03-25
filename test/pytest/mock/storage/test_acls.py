
import pytest

from Acquire.Storage import ACLRule, ACLRules, ACLGroupRules, ACLUserRules


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

    rule = rules.resolve()
    assert(rule.inherits_all())

    data = rules.to_data()
    assert(data == "inherit")

    rules = ACLRules.from_data(data)
    assert(rules.is_simple_inherit())

    user_guid = "someone@somewhere"

    rule = rules.resolve(user_guid=user_guid)
    assert(rule.inherits_all())

    user_rule = ACLUserRules.owner(user_guid=user_guid)
    assert(user_rule.resolve(user_guid=user_guid).is_owner())

    rules.append(user_rule)
    assert(rules.resolve(user_guid=user_guid).is_owner())

    user_guid2 = "someone_else@somewhere"
    assert(rules.resolve(user_guid=user_guid2).denied_all())

    data = rules.to_data()

    rules = ACLRules.from_data(data)

    assert(rules.resolve(user_guid=user_guid).is_owner())
    assert(rules.resolve(user_guid=user_guid2).denied_all())
