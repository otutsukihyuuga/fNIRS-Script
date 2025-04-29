import json
class LSL:
    def __init__(self, outlet):
        self.outlet = outlet
        self.mapping = {}
        self.unique_id = 1
    
    def add_mapping(self, s):
        if s in self.mapping:
            return self.mapping[s]
        else:
            self.mapping[s] = self.unique_id
            self.unique_id += 1
            return self.mapping[s]
    
    def push_sample(self, s):
        number = self.add_mapping(s)
        self.outlet.push_sample(x=[number])
        
    def save(self,path):
        with open(path, 'w') as f:
            json.dump(self.mapping, f)
