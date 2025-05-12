import random
from PIL import Image, ImageDraw, ImageFilter

class AvatarGenerator:
    def __init__(self, size=256, bg_color=(240, 240, 240)):
        self.size = size
        self.bg_color = bg_color
        self.colors = [
            (231, 76, 60),   # красный
            (41, 128, 185),  # синий
            (39, 174, 96),   # зеленый
            (155, 89, 182),  # фиолетовый
            (241, 196, 15),  # желтый
        ]
    
    def generate(self, seed=None):
        if seed:
            random.seed(seed)
        
        # Создаем изображение
        img = Image.new('RGB', (self.size, self.size), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Выбираем случайный цвет
        color = random.choice(self.colors)
        
        # Рисуем основной круг
        circle_size = self.size - random.randint(20, 50)
        circle_pos = ((self.size - circle_size) // 2, (self.size - circle_size) // 2)
        draw.ellipse([circle_pos, (circle_pos[0] + circle_size, circle_pos[1] + circle_size)], fill=color)
        
        # Добавляем внутренний круг
        inner_circle_size = circle_size * 0.7
        inner_circle_pos = ((self.size - inner_circle_size) // 2, (self.size - inner_circle_size) // 2)
        draw.ellipse([inner_circle_pos, (inner_circle_pos[0] + inner_circle_size, inner_circle_pos[1] + inner_circle_size)], fill=self.bg_color)
        
        # Добавляем случайные элементы
        self._add_decoration(draw, color)
        
        # Добавляем размытие для мягкости
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        
        return img
    
    def _add_decoration(self, draw, color):
        # Здесь можно добавить различные декоративные элементы
        # Например, линии, круги или другие фигуры
        elements = random.randint(1, 3)
        
        for _ in range(elements):
            element_type = random.choice(['line', 'circle', 'arc'])
            x = random.randint(0, self.size)
            y = random.randint(0, self.size)
            size = random.randint(10, self.size // 3)
            
            if element_type == 'line':
                draw.line([(x, y), (x + size, y + size)], fill=color, width=random.randint(2, 5))
            elif element_type == 'circle':
                draw.ellipse([(x, y), (x + size, y + size)], outline=color, width=random.randint(2, 5))
            elif element_type == 'arc':
                draw.arc([(x, y), (x + size, y + size)], start=0, end=random.randint(90, 270), fill=color, width=random.randint(2, 5))

# Пример использования
if __name__ == "__main__":
    generator = AvatarGenerator()
    avatar = generator.generate()
    avatar.save("avatar.png")
    avatar.show()
