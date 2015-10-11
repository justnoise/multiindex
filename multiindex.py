from pprint import pprint
#from collections.abc import Iterable
from collections import defaultdict
from sortedcontainers import SortedListWithKey


# MultiIndex has insert, update and delete functions, indexed containers only
# expose an interface appropriate for them
#
# access data by calling multi_index.index_name.get(key)
# maybe a islice and irange methods for the correct containers (returns an iterator)


# problems:
# passing a lot of the implementation over to indexes
# _insert
# _update

class MultiIndex(object):
    def __init__(self, *indexes):
        self.indexes = {}
        for index in indexes:
            self.add_index(index)
        # if isinstance(indexed_by, Iterable):
        #     for index in indexed_by:

        # else:
        #     self.add_index(index)

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
            dest_index.insert(item)

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

    # def iter(self, index):
    #     if type(index) == int:
    #         pass
    #     else:
    #         pass


    # def islice(self, index, start, stop):
    #     pass

    # def irange(self, index, min, max):
    #     pass




# class OrderedUnique(object):
#     unique = True
#     def __init__(self, key, name=None):
#         self.container = SortedListWithKey
#         self.name = name

class OrderedNonUnique(object):

    # gonna have to implement all mapping methods...

    unique = False

    def __init__(self, key, name=None):
        self.key = key
        if not name:
            self.name = key
        else:
            self.name = name
        self._data = SortedListWithKey(key=self._getkey)

    def _getkey(self, value):
        key = getattr(value, self.key)
        return key

    def _insert(self, value):
        self._data.add(value)

    def _update(self, old_value, new_value):
        self._delete(old_value)
        self._insert(new_value)

    def _delete(self, value):
        self._data.remove(value)

    def __getitem__(self, key):
        vals = [item for item in self._data.irange_key(key, key)]
        return vals

    # def debug_print(self):
    #     print "--------------------------------------------------"
    #     print self.__class.__name__
    #     pprint(self)


class HashedUnique(dict):
    unique = True

    def __init__(self, key, name=None):
        self.key = key
        if not name:
            self.name = key
        else:
            self.name = name

    def _insert(self, value):
        k = getattr(value, self.key)
        self[k] = value

    def _update(self, old_value, new_value):
        k = getattr(old_value, self.key)
        self[k] = new_value

    def _delete(self, value):
        k = getattr(value, self.key)
        self.pop(k)


class HashedNonUnique(object):
    unique = False
    def __init__(self, key, name=None):
        self.container = defaultdict(list)  #???
        self.name = name

# directory = MultiIndex(OrderedUnique('phone_number'),
#                        OrderedNonUnique('name'))

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
                    OrderedNonUnique("name"))
    mi.insert(Contact("joe", "home", "123-456-7890"))
    mi.insert(Contact("joe", "work", "123-456-7890"))
    print mi.phone_number.get("123-456-7890")
    print mi.phone_number["123-456-7890"]
    print mi.name["joe"]
    bb = mi.phone_number["123-456-7890"]

    mi.delete(bb)
    mi.debug_print()

if __name__ == '__main__':
    test()
