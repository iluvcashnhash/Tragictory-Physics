"""
Seed data module for Tragictory Physics.

This module provides functions to populate the database with initial
content for testing and demonstration purposes.
"""

from .db_setup import get_connection


def seed_database() -> None:
    """Populate the database with initial test content.
    
    Clears existing data and adds sample grades, topics, theory content,
    and formulas for the physics education application.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Clear all existing data
        cursor.execute("DELETE FROM formulas")
        cursor.execute("DELETE FROM theory_blocks")
        cursor.execute("DELETE FROM topics")
        cursor.execute("DELETE FROM grades")
        
        # Add 10th grade
        cursor.execute(
            "INSERT INTO grades (number, description) VALUES (?, ?)",
            (10, "Кинематика и динамика")
        )
        grade_id = cursor.lastrowid
        
        # Add projectile motion topic
        cursor.execute(
            """INSERT INTO topics (grade_id, title, is_simulation_available) 
               VALUES (?, ?, ?)""",
            (grade_id, "Движение тела, брошенного под углом к горизонту", 1)
        )
        topic_id = cursor.lastrowid
        
        # Add theory content in HTML format
        theory_html = """
        <h2>Баллистическое движение</h2>
        
        <p><strong>Баллистическое движение</strong> — это движение тела в поле силы тяжести 
        под действием только силы тяжести (сопротивлением воздуха пренебрегаем).</p>
        
        <h3>Ключевые принципы</h3>
        
        <p>При анализе баллистического движения используется принцип <strong>независимости 
        движений по взаимно перпендикулярным направлениям</strong>:</p>
        
        <ul>
            <li><strong>Движение по оси X:</strong> происходит равномерно с постоянной скоростью 
            v<sub>x</sub> = v<sub>0</sub> cos(α), так как сила тяжести не имеет горизонтальной составляющей.</li>
            <li><strong>Движение по оси Y:</strong> происходит равноускоренно с ускорением 
            свободного падения g, направленным вниз.</li>
        </ul>
        
        <h3>Уравнения движения</h3>
        
        <p>Координаты тела в любой момент времени t:</p>
        
        <blockquote>
            <p><strong>x(t) = v<sub>0</sub> cos(α) · t</strong></p>
            <p><strong>y(t) = v<sub>0</sub> sin(α) · t - (g · t²)/2</strong></p>
        </blockquote>
        
        <p>где:
        - v<sub>0</sub> — начальная скорость
        - α — угол броска к горизонту
        - g — ускорение свободного падения
        - t — время</p>
        
        <h3>Особенности траектории</h3>
        
        <p>Траектория тела представляет собой <strong>параболу</strong>. Форма параболы 
        зависит от начальной скорости и угла броска:</p>
        
        <ul>
            <li>При угле 45° достигается максимальная дальность полета</li>
            <li>При углах 30° и 60° дальность одинакова, но максимальная высота различна</li>
            <li>Время подъема до верхней точки равно времени спуска</li>
        </ul>
        
        <h3>Практическое применение</h3>
        
        <p>Знание баллистического движения необходимо для:</p>
        <ul>
            <li>Расчета траектории снарядов и ракет</li>
            <li>Определения оптимальных углов броска в спорте</li>
            <li>Понимания движения планет и спутников</li>
        </ul>
        """
        
        cursor.execute(
            "INSERT INTO theory_blocks (topic_id, content_html) VALUES (?, ?)",
            (topic_id, theory_html)
        )
        
        # Add formulas in LaTeX format
        formulas = [
            {
                'formula_latex': r'y(x) = x \cdot \tan(\alpha) - \frac{g \cdot x^2}{2v_0^2 \cos^2(\alpha)}',
                'description': 'Уравнение траектории (зависимость высоты от дальности)'
            },
            {
                'formula_latex': r'h_{max} = \frac{v_0^2 \sin^2(\alpha)}{2g}',
                'description': 'Максимальная высота подъема'
            },
            {
                'formula_latex': r'L = \frac{v_0^2 \sin(2\alpha)}{g}',
                'description': 'Дальность полета'
            }
        ]
        
        for formula in formulas:
            cursor.execute(
                """INSERT INTO formulas (topic_id, formula_latex, description) 
                   VALUES (?, ?, ?)""",
                (topic_id, formula['formula_latex'], formula['description'])
            )
        
        conn.commit()
        print("Database seeded successfully!")
        print(f"Added grade: 10 класс")
        print(f"Added topic: Движение тела, брошенного под углом к горизонту")
        print(f"Added {len(formulas)} formulas")
        
    except Exception as e:
        conn.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed_database()
