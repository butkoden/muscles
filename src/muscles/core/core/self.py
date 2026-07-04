class Prop:
    pass


class Self(Prop):
    """
    Класс позволяющий добавить в объект ссылку на самого себя

    """

    _instance = None
    _name = None
    app = None
    public_name = None
    private_name = None

    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = '_' + name

    def __get__(self, obj, objtype=None):
        return self.app

    def __deepcopy__(self, memo):
        copy_method = getattr(self, "copy", None)
        if callable(copy_method):
            return copy_method()
        return self
