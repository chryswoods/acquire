
from Acquire.Identity import ACLRule, ACLRules, ACLUserRules
import json


def test_aclrules():
    user1_guid = "12345@z0-z0"
    user2_guid = "67890@z0-z0"

    rule1 = ACLRules.owner(user_guid=user1_guid)
    rule2 = ACLRules.owner(user_guid=user2_guid)

    identifiers1 = {"user_guid": user1_guid}
    identifiers2 = {"user_guid": user2_guid}

    assert(rule1.resolve(identifiers=identifiers1).is_owner())
    assert(rule1.resolve(identifiers=identifiers2).is_denied())

    assert(rule2.resolve(identifiers=identifiers1).is_denied())
    assert(rule2.resolve(identifiers=identifiers2).is_owner())

    rule3 = ACLRules.owner(user_guid=user1_guid,
                           default_rule=ACLRule.reader())
    rule4 = ACLRules.owner(user_guid=user2_guid,
                           default_rule=ACLRule.writer())

    assert(rule3.resolve(identifiers=identifiers1).is_owner())
    assert(rule3.resolve(identifiers=identifiers2).is_readable())

    assert(rule4.resolve(identifiers=identifiers1).is_writeable())
    assert(rule4.resolve(identifiers=identifiers2).is_owner())

    rule5 = ACLRules.owner(user_guid=user1_guid).append(
                            ACLRules.reader(user_guid=user2_guid))
    rule6 = ACLRules.owner(user_guid=user2_guid).append(
                            ACLRules.writer(user_guid=user1_guid))

    user3_guid = "67890@a0-a0"
    identifiers3 = {"user_guid": user3_guid}

    assert(rule5.resolve(identifiers=identifiers1).is_owner())
    assert(rule5.resolve(identifiers=identifiers2).is_readable())
    assert(rule5.resolve(identifiers=identifiers3).is_denied())

    assert(rule6.resolve(identifiers=identifiers1).is_writeable())
    assert(rule6.resolve(identifiers=identifiers2).is_owner())
    assert(rule6.resolve(identifiers=identifiers3).is_denied())

    user_rule = ACLUserRules.owner(user_guid=user1_guid).add(
                         user_guid=user2_guid, rule=ACLRule.reader())
    rule7 = ACLRules(rule=user_rule, default_rule=ACLRule.denied())

    assert(rule7.resolve(identifiers=identifiers1).is_owner())
    assert(rule7.resolve(identifiers=identifiers2).is_readable())
    assert(rule7.resolve(identifiers=identifiers3).is_denied())
