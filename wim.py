class WIM:
    def __init__(self, output_dict) -> None:
        for k, v in output_dict.items():
            setattr(self, k.replace(' ', '_'), v)

    def __repr__(self):
        return '{' + self.Name + ', ' + self.Architecture + ', ' + self.Languages + '}'
    
    def __str__(self) -> str:
        return self.Name + ', ' + self.Architecture + ', ' + self.Languages + ', ' + self.Version + ', ' + self.Modified + ' from ' + self.Details_for_image + ':' + self.Index

if __name__ == '__main__':
    pass