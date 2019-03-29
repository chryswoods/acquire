
from enum import Enum as _Enum

__all__ = ["ACLRules", "ACLUserRules", "ACLGroupRules",
           "create_aclrules"]


class ACLRuleOperation(_Enum):
    MAX = "max"  # add rules together (most permissive)
    MIN = "min"  # add rules together (least permissive)
    SUB = "sub"  # subtract rules (why?)
    SET = "set"  # break - set first matching fully-resolved rule

    def to_data(self):
        return self.value

    def combine(self, acl1, acl2):
        if acl1 is None:
            return acl2
        elif acl2 is None:
            return acl1

        if self is ACLRuleOperation.SET:
            return acl1
        elif self is ACLRuleOperation.MAX:
            return acl1 + acl2
        elif self is ACLRuleOperation.MIN:
            return acl1 * acl2
        elif self is ACLRuleOperation.SUB:
            return acl1 - acl2
        else:
            return None

    @staticmethod
    def from_data(data):
        return ACLRuleOperation(data)


def create_aclrules(**kwargs):
    """Create an ACLRules object the passed set of rules, for example

        user_guid, aclrule  would set the aclrule for user to aclrule
        group_guid, aclrule would set the aclrule for group to aclrule

        default_rule  would set a default rule if nothing else matches
    """
    aclrules = None

    if "aclrules" in kwargs:
        aclrules = kwargs["aclrules"]

        if not isinstance(aclrules, ACLRules):
            aclrules = ACLRules(rule=aclrules)

        if "default" in kwargs:
            aclrules.set_default_rule(kwargs["default"])

    if "aclrule" in kwargs:
        from Acquire.Storage import ACLRule as _ACLRule

        aclrule = kwargs["aclrule"]
        if "user_guid" in kwargs:
            if aclrules is None:
                aclrules = ACLRules(default_rule=_ACLRule.denied())

            user_rules = ACLUserRules()
            user_rules.add_user_rule(kwargs["user_guid"], aclrule)
            aclrules.append(user_rules)
        elif "group_guid" in kwargs:
            if aclrules is None:
                aclrules = ACLRules(default_rule=_ACLRule.denied())

            group_rules = ACLGroupRules()
            group_rules.add_group_rule(kwargs["group_guid"], aclrule)
            aclrules.append(group_rules)
        else:
            if isinstance(aclrule, ACLRules):
                aclrules.append(aclrule)

    if "default" in kwargs:
        if aclrules is None:
            aclrules = ACLRules(default_rule=kwargs["default"])
        else:
            aclrules.set_default(kwargs["default"])

    if aclrules is None:
        aclrules = ACLRules()

    return aclrules


def _save_rule(rule):
    """Return a json-serialisable object for the passed rule"""
    return [rule.__class__.__name__, rule.to_data()]


def _load_rule(rule):
    """Return the rule loaded from the json-deserialised data"""
    try:
        classname = rule[0]
        classdata = rule[1]
    except:
        raise TypeError("Expected [classname, classdata]")

    if classname == "ACLRules":
        return ACLRules.from_data(classdata)
    elif classname == "ACLUserRules":
        return ACLUserRules.from_data(classdata)
    elif classname == "ACLGroupRules":
        return ACLGroupRules.from_data(classdata)
    elif classname == "ACLRule":
        from Acquire.Storage import ACLRule as _ACLRule
        return _ACLRule.from_data(classdata)
    else:
        raise TypeError("Unrecognised type '%s'" % classname)


class ACLGroupRules:
    """This class holds rules that apply to individual groups"""
    def __init__(self):
        """Construct, optionally starting with a default rule
           is no groups are matched
        """
        self._group_rules = {}

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __str__(self):
        s = []
        for group, rule in self._group_rules.items():
            s.append("%s => %s" % (group, rule))
        return "Group{%s}" % ", ".join(s)

    def resolve(self, must_resolve=True, **kwargs):
        """Resolve the rule for the user with specified group_guid.
           This returns None if there are no rules for this group
        """
        try:
            group_guid = kwargs["group_guid"]
        except:
            group_guid = None

        if group_guid in self._group_rules:
            rule = self._group_rules[group_guid]
            return rule.resolve(must_resolve=must_resolve, **kwargs)
        elif must_resolve:
            from Acquire.Storage import ACLRule as _ACLRule
            return _ACLRule.inherit().resolve(must_resolve=True, **kwargs)
        else:
            return None

    def add_group_rule(self, group_guid, rule):
        """Add a rule for the used with passed 'group_guid'"""
        self._group_rules[group_guid] = rule

    def to_data(self):
        """Return a json-serialisable representation of these rules"""
        data = {}

        for group_guid, rule in self._group_rules.items():
            data[group_guid] = _save_rule(rule)

        return data

    @staticmethod
    def from_data(data):
        """Return the rules constructed from the passed json-deserialised
           object
        """
        rules = ACLGroupRules()

        if data is not None and len(data) > 0:
            for group_guid, rule in data.items():
                rules.add_group_rule(group_guid, _load_rule(rule))

        return rules


class ACLUserRules:
    """This class holds rules that apply to individual users"""
    def __init__(self):
        """Construct, optionally starting with a default rule
           if no users are matched
        """
        self._user_rules = {}

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __str__(self):
        s = []
        for user, rule in self._user_rules.items():
            s.append("%s => %s" % (user, rule))
        return "User{%s}" % ", ".join(s)

    def resolve(self, must_resolve=True, **kwargs):
        """Resolve the rule for the user with specified user_guid.
           This returns None if there are no rules for this user
        """
        try:
            user_guid = kwargs["user_guid"]
        except:
            user_guid = None

        if user_guid in self._user_rules:
            rule = self._user_rules[user_guid]
            return rule.resolve(must_resolve=must_resolve, **kwargs)
        elif must_resolve:
            from Acquire.Storage import ACLRule as _ACLRule
            return _ACLRule.inherit().resolve(must_resolve=True, **kwargs)
        else:
            return None

    def add_user_rule(self, user_guid, rule):
        """Add a rule for the used with passed 'user_guid'"""
        self._user_rules[user_guid] = rule

    @staticmethod
    def _create(aclrule, user_guid, user_guids):
        rule = ACLUserRules()

        if user_guid is not None:
            rule.add_user_rule(user_guid, aclrule)

        if user_guids is not None:
            for user_guid in user_guids:
                rule.add_user_rule(user_guid, aclrule)

        return rule

    @staticmethod
    def owner(user_guid=None, user_guids=None):
        """Simple shorthand to create the rule that the specified
           user is the owner of the resource
        """
        from Acquire.Storage import ACLRule as _ACLRule
        return ACLUserRules._create(aclrule=_ACLRule.owner(),
                                    user_guid=user_guid,
                                    user_guids=user_guids)

    @staticmethod
    def executer(user_guid=None, user_guids=None):
        """Simple shorthand to create the rule that the specified
           user is the executer of the resource
        """
        from Acquire.Storage import ACLRule as _ACLRule
        return ACLUserRules._create(aclrule=_ACLRule.executer(),
                                    user_guid=user_guid,
                                    user_guids=user_guids)

    @staticmethod
    def writer(user_guid=None, user_guids=None):
        """Simple shorthand to create the rule that the specified
           user is the writer of the resource
        """
        from Acquire.Storage import ACLRule as _ACLRule
        return ACLUserRules._create(aclrule=_ACLRule.writer(),
                                    user_guid=user_guid,
                                    user_guids=user_guids)

    @staticmethod
    def reader(user_guid=None, user_guids=None):
        """Simple shorthand to create the rule that the specified
           user is the reader of the resource
        """
        from Acquire.Storage import ACLRule as _ACLRule
        return ACLUserRules._create(aclrule=_ACLRule.reader(),
                                    user_guid=user_guid,
                                    user_guids=user_guids)

    def to_data(self):
        """Return a json-serialisable representation of these rules"""
        data = {}

        for user_guid, rule in self._user_rules.items():
            data[user_guid] = _save_rule(rule)

        return data

    @staticmethod
    def from_data(data):
        """Return the rules constructed from the passed json-deserialised
           object
        """
        rules = ACLUserRules()

        if data is not None and len(data) > 0:
            for user_guid, rule in data.items():
                rules.add_user_rule(user_guid, _load_rule(rule))

        return rules


def _is_inherit(aclrule):
    """Return whether or not this passed rule is just an inherit-all"""
    from Acquire.Storage import ACLRule as _ACLRule

    if isinstance(aclrule, _ACLRule):
        if aclrule == _ACLRule.inherit():
            return True

    return False


class ACLRules:
    """This class holds a combination of ACL rules. These are parsed
       in order to get the ACL for a resource.

       By default, this is a simple inherit rule (meaning that
       it will inherit whatever comes from upstream)
    """
    def __init__(self, rule=None, rules=None, default_rule=None,
                 default_operation=ACLRuleOperation.MAX):
        """Construct, optionally starting with a default ACLRule
           for all users
        """
        if default_rule is None:
            self._is_simple_inherit = True
        elif _is_inherit(default_rule):
            self._is_simple_inherit = True
        else:
            self._is_simple_inherit = False
            self._default_rule = default_rule
            self._rules = []

        self.set_default_operation(default_operation)

        if rule is not None:
            self.prepend(rule)

        if rules is not None:
            for rule in rules:
                self.append(aclrule=rule[1], operation=rule[0])

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __str__(self):
        if self._is_simple_inherit:
            return "inherit"

        s = []
        for rule in rules:
            s.append("%s" % rule)

        if self._default_rule is not None:
            s.append("DEFAULT %s" % self._default_rule)

        return s

    def is_simple_inherit(self):
        """Return whether or not this set of rules is a simple
           'inherit all'
        """
        return self._is_simple_inherit

    def set_default_operation(self, default_operation):
        """Set the default operation used to combine together rules"""
        if not isinstance(default_operation, ACLRuleOperation):
            raise TypeError(
                "The default operation must be type ACLRuleOperation")

        self._default_operation = default_operation

    def set_default_rule(self, aclrule):
        """Set the default rule if nothing else matches (optionally
           also specifying the default operation to combine rules)
        """
        if self._is_simple_inherit:
            if _is_inherit(aclrule):
                return
            else:
                self._is_simple_inherit = False
                self._default_rule = aclrule
                self._default_operation = ACLRuleOperation.MAX
                self._rules = []
        else:
            self._default_rule = aclrule

    def append(self, aclrule, operation=None, ensure_owner=False):
        """Append a rule onto the set of rules. This will resolve any
           conflicts in the rules. If 'ensure_owner' is True, then
           this will ensure that there is at least one user who
           has unambiguous ownership of the resource controlled by
           these ACL rules
        """
        try:
            idx = len(self._rules)
        except:
            idx = 2

        self.insert(idx=idx, aclrule=aclrule,
                    operation=operation, ensure_owner=ensure_owner)

    def prepend(self, aclrule, operation=None, ensure_owner=False):
        """Prepend a rule onto the set of rules"""
        self.insert(idx=0, aclrule=aclrule,
                    operation=operation, ensure_owner=ensure_owner)

    def insert(self, idx, aclrule, operation=None, ensure_owner=False):
        """Insert the passed rule at index 'idx', specifying the operation
           used to combine this rule with what has gone before
           (defaults to self._default_operation)
        """
        if operation is not None:
            if not isinstance(operation, ACLRuleOperation):
                raise TypeError(
                    "The ACL operation must be type ACLRuleOperation")

        if self._is_simple_inherit:
            if _is_inherit(aclrule):
                return
            else:
                from Acquire.Storage import ACLRule as _ACLRule
                self._is_simple_inherit = False
                self._default_rule = None
                self._rules = [_ACLRule.inherit()]

        if operation is not None:
            self._rules.insert(idx, (operation, aclrule))
        else:
            self._rules.insert(idx, aclrule)

        if ensure_owner:
            # need to write code to ensure there is at least one owner
            pass

    def rules(self):
        """Return the list of ACL rules that will be applied
           in order (including the default rule, if set)
        """
        if self._is_simple_inherit:
            from Acquire.Storage import ACLRule as _ACLRule
            return [(self._default_operation, _ACLRule.inherit())]
        else:
            import copy as copy
            r = copy.copy(self._rules)
            if self._default_rule is not None:
                r.append((self._default_operation, self._default_rule))

            return r

    def resolve(self, must_resolve=True, **kwargs):
        """Resolve the rule based on the passed kwargs. This will
           resolve the rules in order the final ACLRule has been
           generated. If 'must_resolve' is True, then
           this is guaranteed to return a fully-resolved simple ACLRule
        """
        from Acquire.Storage import ACLRule as _ACLRule

        if self._is_simple_inherit:
            return _ACLRule.inherit().resolve(must_resolve=must_resolve,
                                              **kwargs)

        result = None
        must_break = False

        for rule in self._rules:
            if isinstance(rule, tuple):
                op = rule[0]
                rule = rule[1]
            else:
                op = self._default_operation

            # resolve the rule...
            rule = rule.resolve(must_resolve=False, **kwargs)

            if rule is not None:
                if op is ACLRuleOperation.SET:
                    # take the first matching rule
                    result = rule
                    must_break = True
                    break
                elif result is None:
                    result = rule
                else:
                    result = op.combine(result, rule)

        if (not must_break) and (self._default_rule is not None):
            rule = self._default_rule.resolve(must_resolve=False, **kwargs)
            if result is None:
                result = rule
            else:
                result = self._default_operation.combine(result, rule)

        # should now have a fully resolved ACLRule...
        if result is None:
            return _ACLRule.denied()

        if not isinstance(result, _ACLRule):
            raise PermissionError(
                "Did not fully resolve the ACLRule - got %s" % str(result))

        if not result.is_fully_resolved():
            result = result.resolve(must_resolve=True, **kwargs)

        # we have not been able to generate a fully-resolved ACL
        return result

    @staticmethod
    def from_data(data):
        """Construct these rules from the passed json-serialised
           dictionary
        """
        if isinstance(data, str) and data == "inherit":
                return ACLRules()

        if data is not None and len(data) > 0:

            if "default_rule" in data:
                default_rule = _load_rule(data["default_rule"])
            else:
                default_rule = None

            if "default_operation" in data:
                default_operation = \
                    ACLRuleOperation.from_data(data["default_operation"])
            else:
                default_operation = ACLRuleOperation.MAX

            if "rules" in data:
                rules = []
                for rule in data["rules"]:
                    if isinstance(rule, tuple):
                        rules.append((ACLRuleOperation.from_data(rule[0]),
                                      _load_rule(rule[1])))
                    else:
                        rules.append((None, _load_rule(rule)))
            else:
                rules = None

            return ACLRules(default_rule=default_rule,
                            default_operation=default_operation,
                            rules=rules)
        else:
            return ACLRules()

    def to_data(self):
        """Return a json-serialisable dictionary of these rules"""
        if self._is_simple_inherit:
            return "inherit"

        data = {}

        if len(self._rules) > 0:
            rules = []

            for rule in self._rules:
                if isinstance(rule, tuple):
                    rules.append((rule[0].to_data(), _save_rule(rule[1])))
                else:
                    rules.append(_save_rule(rule))

            data["rules"] = rules

        if self._default_rule is not None:
            data["default_rule"] = _save_rule(self._default_rule)

        if self._default_operation is not ACLRuleOperation.MAX:
            data["default_operation"] = self._default_operation.to_data()

        return data
