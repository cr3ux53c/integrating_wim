class WIM:
    def __init__(self, output_dict) -> None:
        for k, v in output_dict.items():
            setattr(self, k.replace(' ', '_'), v)

    def __repr__(self):
        return '{' + self.Name + ', ' + self.Architecture + ', ' + self.Languages + '}'
    
    def __str__(self) -> str:
        return self.Name + ', ' + self.Architecture + ', ' + self.Languages

if __name__ == '__main__':
    pass