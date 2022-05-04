class WIM:
    def __init__(self, output_dict) -> None:
        self.__dict__.update(output_dict)

    def __repr__(self):
        return '{' + self.Name + ', ' + self.Architecture + ', ' + self.Languages + '}'

if __name__ == '__main__':
    args = ['fdas', 'fdfd']
    wim = WIM(*args)
    print(wim)