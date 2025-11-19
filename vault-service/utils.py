import random
import string
import re


class PasswordUtils:
    @staticmethod
    def generate(length: int = 16) -> str:
        if length < 8:
            length = 8

        lower = string.ascii_lowercase
        upper = string.ascii_uppercase
        digits = string.digits
        symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"

        # Ensure at least one of each
        password = [
            random.choice(lower),
            random.choice(upper),
            random.choice(digits),
            random.choice(symbols)
        ]

        # Fill the rest
        all_chars = lower + upper + digits + symbols
        password += [random.choice(all_chars) for _ in range(length - 4)]

        # Shuffle
        random.shuffle(password)
        return "".join(password)

    @staticmethod
    def strength(password: str) -> dict:
        score = 0
        feedback = []

        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1

        if re.search(r"[a-z]", password):
            score += 1
        if re.search(r"[A-Z]", password):
            score += 1
        if re.search(r"\d", password):
            score += 1
        if re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?'\"]", password):
            score += 1

        strength_levels = [
            "Very Weak", "Weak", "Fair", "Good", "Strong", "Very Strong", "Excellent"
        ]
        colors = [
            "#ff0000", "#ff4444", "#ff8800", "#ffbb33", "#99cc00", "#33b5e5", "#00C851"
        ]

        level = min(score, len(strength_levels) - 1)

        return {
            "score": score,
            "level": strength_levels[level],
            "color": colors[level],
            "percentage": min(score * 14.28, 100)  # 0-100%
        }