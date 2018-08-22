
class Vkmap():
    map_ = {'y': 89, 'l': 76, 'z': 90, 'i': 73, 'j': 74,
            'f': 70, 'a': 65, 'v': 86, 't': 84, 'r': 82,
            'k': 75, 'q': 81, 'd': 68, 'm': 77, 'b': 66,
            'e': 69, 'n': 78, 'u': 85, 'p': 80, 'c': 67,
            's': 83, 'h': 72, 'o': 79, 'x': 88, 'g': 71,
            'w': 87}

    def get_vk(char):
        char = char.lower()
        return Vkmap.map_[char]

    def has(char):
        char = char.lower()
        return char in Vkmap.map_
        
