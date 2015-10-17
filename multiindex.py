from pprint import pprint
from collections import defaultdict
from sortedcontainers import SortedListWithKey


# MultiIndex has insert, update and delete functions, indexed containers only
# expose an interface appropriate for them
#
# access data by calling multi_index.index_name.get(key)
# maybe a islice and irange methods for the correct containers (returns an iterator)


class MultiIndex(object):
    def __init__(self, *indexes):
        self.indexes = {}
        for index in indexes:
            self.add_index(index)

    def __getattr__(self, indexname):
        """provide access to indexes"""
        if indexname in self.indexes:
            return self.indexes[indexname]
        raise AttributeError

    def insert(self, value):
        for index in self.indexes.itervalues():
            index._insert(value)

    def update(self, old_value, new_value):
        #need to remove the item from all indexes and re-insert it
        for index in self.indexes.itervalues():
            index._update(old_value, new_value)

    def delete(self, value):
        for index in self.indexes.itervalues():
            index._delete(value)

    def _copy_data_to_index(self, src_index, dest_index):
        for item in src_index:
            dest_index._insert(item)

    def add_index(self, new_index):
        if new_index.name in self.indexes:
            raise NotImplementedError("cannot replace existing index")

        # if we have existing data, copy it
        # if this is a unique index, copy data from existing unique index
        # otherwise, just copy from non-unique
        unique_indexes = [index for index in self.indexes.itervalues()
                          if index.unique]
        if new_index.unique and unique_indexes:
            self._copy_data_to_index(unique_indexes[0], new_index)
        else:
            nonunique_indexes = [index for index in self.indexes.itervalues()
                                 if not index.unique]
            if nonunique_indexes:
                self._copy_data_to_index(nonunique_indexes[0], new_index)
        self.indexes[new_index.name] = new_index

    def debug_print(self):
        for k, v in self.indexes.iteritems():
            print "--------------------------------------------------"
            print v.__class__.__name__
            pprint(v)


class Index(object):
    def __init__(self, key, name):
        self.key = key
        if not name:
            self.name = key
        else:
            self.name = name

    def _getkey(self, value):
        key = getattr(value, self.key)
        return key


class OrderedNonUnique(Index):
    unique = False

    def __init__(self, key, name=None):
        super(OrderedNonUnique, self).__init__(key, name)
        self._data = SortedListWithKey(key=self._getkey)

    def _insert(self, value):
        self._data.add(value)

    def _update(self, old_value, new_value):
        self._delete(old_value)
        self._insert(new_value)

    def _delete(self, value):
        self._data.remove(value)

    def __getitem__(self, key):
        """Not sure if we should return an iterator
        or a list of values... I'm thinking iterator!"""
        return self.irange_key(key, key)

    def __len__(self):
        return len(self._data)

    def __contains__(self, value):
        return value in self._data

    def __reversed__(self):
        return reversed(self._data)

    def __iter__(self):
        return self._data.irange()

    def __repr__(self):
        return self._data.__repr__()

    def count(self, val):
        return self._data.count(val)

    def count_key(self, key):
        itr = self._data.irange_key(key, key)
        num_items = 0
        for _ in itr:
            num_items += 1
        return num_items

    def islice(self, start=None, stop=None, reverse=False):
        return self._data.islice(start, stop, reverse)

    def irange(self, minimum=None, maximum=None, inclusive=(True, True), reverse=False):
        return self._data.irange(minimum, maximum, inclusive, reverse)


    def irange_key(self, min_key=None, max_key=None, inclusive=(True, True),
                   reverse=False):
        return self._data.irange_key(min_key, max_key, inclusive, reverse)


class HashedUnique(Index, dict):
    """For now, we'll derive from dict even tho it means
    users can do stuff they shouldn't, like insert values
    into the index"""
    unique = True

    def __init__(self, key, name=None):
        super(HashedUnique, self).__init__(key, name)

    def _insert(self, value):
        k = getattr(value, self.key)
        self[k] = value

    def _update(self, old_value, new_value):
        self._delete(old_value)
        self._insert(new_value)

    def _delete(self, value):
        k = getattr(value, self.key)
        self.pop(k)


class HashedNonUnique(Index):
    unique = False

    def __init__(self, key, name=None):
        super(HashedNonUnique, self).__init__(key, name)
        self._data = defaultdict(list)
        self.num_items = 0

    def _insert(self, value):
        k = getattr(value, self.key)
        self._data[k].append(value)
        self.num_items += 1

    def _update(self, old_value, new_value):
        self._delete(old_value)
        self._insert(new_value)

    def _delete(self, value):
        key = self._getkey(value)
        num_items_at_key = len(self._data[key])
        remaining_vals = [item for item in self._data[key]
                          if item != value]
        num_items_removed = num_items_at_key - len(remaining_vals)
        self.num_items -= num_items_removed
        self._data[key] = remaining_vals

    def __len__(self):
        return self.num_items

    def __getitem__(self, key):
        """Not sure if we should return an iterator
        or a list of values... I'm thinking iterator!"""
        return iter(self._data[key])

    def __contains__(self, value):
        key = self._getkey(value)
        return value in self._data[key]

    def __iter__(self):
        for k, _ in self.iteritems():
            yield k

    def iteritems(self):
        for key, value_list in self._data:
            for value in value_list:
                yield key, value

    def iterkeys(self):
        return self.__iter__()

    def itervalues(self):
        for _, v in self.iteritems():
            yield v

    def keys(self):
        return list(self.__iter__())

    def values(self):
        return list(self.itervalues())

    def items(self):
        return list(self.iteritems())

    def unique_keys(self):
        return self._data.keys()

    def __repr__(self):
        return self._data.__repr__()

    def count(self, value):
        key = self._getkey(value)
        count = 0
        for item in self._data[key]:
            if value == item:
                count += 1
        return count


class Contact(object):
    def __init__(self, name, address, phone_number):
        self.name = name
        self.address = address
        self.phone_number = phone_number

    def _get_str(self):
        return "{} | {} | {}".format(self.name, self.address, self.phone_number)
    def __str__(self):
        return self._get_str()
    def __repr__(self):
        return self._get_str()


def test():
    mi = MultiIndex(HashedUnique("phone_number"),
                    OrderedNonUnique("name"),
                    OrderedNonUnique("address"))
    mi.insert(Contact("joe", "home", "123-456-7890"))
    mi.insert(Contact("joe", "work", "123-456-7890"))
    mi.insert(Contact("bob", "work", "555-123-8888"))
    print mi.phone_number.get("123-456-7890")
    print mi.phone_number["123-456-7890"]
    print mi.name["joe"]
    print "people at work"
    for x in mi.address.irange_key("work", "work"):
        print x
    bb = mi.phone_number["123-456-7890"]
    mi.delete(bb)
    mi.debug_print()

if __name__ == '__main__':
    test()
