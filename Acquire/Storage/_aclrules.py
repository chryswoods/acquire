
__all__ = ["ACLRules", "ACLUserRules", "ACLGroupRules"]


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

    def resolve(self, **kwargs):
        """Resolve the rule for the user with specified group_guid.
           This returns 'default_rule' if there are no rules for this group
        """
        try:
            group_guid = kwargs["group_guid"]
        except:
            group_guid = None

        if group_guid in self._group_rules:
            return self._group_rules[group_guid].resolve(kwargs)
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

    def resolve(self, **kwargs):
        """Resolve the rule for the user with specified user_guid.
           This returns 'default_rule' if there are no rules for this user
        """
        try:
            user_guid = kwargs["user_guid"]
        except:
            user_guid = None

        if user_guid in self._user_rules:
            rule = self._user_rules[user_guid]
            print(rule)
            return rule.resolve(**kwargs)
        else:
            return None

    def add_user_rule(self, user_guid, rule):
        """Add a rule for the used with passed 'user_guid'"""
        self._user_rules[user_guid] = rule

    @staticmethod
    def owner(user_guid):
        """Simple shorthand to create the rule that the specified
           user is the owner of the resource
        """
        from Acquire.Storage import ACLRule as _ACLRule
        rule = ACLUserRules()
        rule.add_user_rule(user_guid, _ACLRule.owner())
        return rule

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
    def __init__(self, default_rule=None):
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

    def is_simple_inherit(self):
        """Return whether or not this set of rules is a simple
           'inherit all'
        """
        return self._is_simple_inherit

    def set_default(self, aclrule):
        """Set the default rule if nothing else matches"""
        if self._is_simple_inherit:
            if _is_inherit(aclrule):
                return
            else:
                self._is_simple_inherit = False
                self._default_rule = aclrule
                self._rules = []

    def append(self, aclrule):
        """Append a rule onto the set of rules"""
        if self._is_simple_inherit:
            if _is_inherit(aclrule):
                return
            else:
                self._is_simple_inherit = False
                self._default_rule = None
                self._rules = []

        self._rules.append(aclrule)

    def prepend(self, aclrule):
        """Prepend a rule onto the set of rules"""
        self.insert(0, aclrule)

    def insert(self, i, aclrule):
        """Insert the passed rule at index 'i'"""
        if self._is_simple_inherit:
            if _is_inherit(aclrule):
                return
            else:
                self._is_simple_inherit = False
                self._default_rule = None
                self._rules = []

        self._rules.insert(i, aclrule)

    def rules(self):
        """Return the list of ACL rules that will be applied
           in order (including the default rule, if set)
        """
        if self._is_simple_inherit:
            from Acquire.Storage import ACLRule as _ACLRule
            return [_ACLRule.inherit()]
        else:
            import copy as copy
            r = copy.copy(self._rules)
            if self._default_rule is not None:
                r.append(self._default_rule)

            return r

    def resolve(self, **kwargs):
        """Resolve the rule based on the passed kwargs. This will
           resolve the rules in order until a fully resolved ACLRule
           has been generated. This is guaranteed to return a
           fully-resolved simple ACLRule
        """
        from Acquire.Storage import ACLRule as _ACLRule

        if self._is_simple_inherit:
            return _ACLRule.inherit()

        for rule in self._rules:
            r = rule.resolve(**kwargs)

            if r is not None:
                if isinstance(r, _ACLRule):
                    if r.is_fully_resolved():
                        return r

                kwargs["upstream"] = r

        # we have not found a matching rule...
        if self._default_rule is not None:
            r = self._default_rule.resolve(**kwargs)

            if isinstance(r, _ACLRule):
                if r.is_fully_resolved():
                    return r

        # we have not been able to generate a fully-resolved ACL
        return _ACLRule.denied()

    @staticmethod
    def from_data(data):
        """Construct these rules from the passed json-serialised
           dictionary
        """
        rules = ACLRules()

        if data is not None and len(data) > 0:
            if isinstance(data, str) and (data == "inherit"):
                return rules

            if "rules" in data:
                for rule in data["rules"]:
                    rules.append(_load_rule(rule))

            if "default_rule" in data:
                rules.set_default(_load_rule(data["default_rule"]))

        return rules

    def to_data(self):
        """Return a json-serialisable dictionary of these rules"""
        if self._is_simple_inherit:
            return "inherit"

        data = {}

        if len(self._rules) > 0:
            rules = []

            for rule in self._rules:
                rules.append(_save_rule(rule))

            data["rules"] = rules

        if self._default_rule is not None:
            data["default_rule"] = _save_rule(self._default_rule)

        return data
