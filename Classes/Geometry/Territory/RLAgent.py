import random
from collections import defaultdict

class RLAgent:
    def __init__(self,
                 alpha=0.1,
                 gamma=0.9,
                 epsilon=0.2,
                 log_filename="rlagent_log.txt"):
        """
        Простейший Q-Learning агент + логирование.
        """
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon

        self.Q = defaultdict(float)

        self.last_state = None
        self.last_action = None

        # Логирование
        self.log_filename = log_filename
        # Открываем файл на добавление
        self.log_file = open(self.log_filename, "a", encoding="utf-8")

        # Для удобства можно записать "шапку" лог-файла
        self.log_file.write("\n==== New RLAgent session starts ====\n")

    def act(self, state, possible_actions):
        """
        Возвращаем одно из possible_actions методом eps-greedy
        и логируем выбор.
        """
        if random.random() < self.epsilon:
            action = random.choice(possible_actions)
        else:
            # поиск действия с макс. Q
            best_a = None
            best_q = float('-inf')
            for a in possible_actions:
                q_val = self.Q[(state, a)]
                if q_val > best_q:
                    best_q = q_val
                    best_a = a
            action = best_a if best_a is not None else random.choice(possible_actions)

        # Запишем в лог инфо о выборе
        self.log_file.write(f"[ACT] state={state}, possible={possible_actions}, chosen={action}\n")

        self.last_state = state
        self.last_action = action
        return action

    def store_transition(self, reward, new_state, done=False):
        """
        Обновляем Q(s,a) по формуле Q-Learning + логируем.
        """
        if self.last_state is None or self.last_action is None:
            return

        s = self.last_state
        a = self.last_action
        old_q = self.Q[(s, a)]

        # Считаем max Q(new_state, *)
        if done:
            max_q_next = 0.0
        else:
            q_candidates = []
            for (st, act), q_val in self.Q.items():
                if st == new_state:
                    q_candidates.append(q_val)
            max_q_next = max(q_candidates) if q_candidates else 0.0

        new_q = old_q + self.alpha * (reward + self.gamma * max_q_next - old_q)
        self.Q[(s, a)] = new_q

        # Логируем
        self.log_file.write(f"[STORE] s={s}, a={a}, r={reward}, new_s={new_state}, done={done}, oldQ={old_q:.3f}, newQ={new_q:.3f}\n")

        if done:
            # сброс
            self.last_state = None
            self.last_action = None
        else:
            # продолжаем
            self.last_state = new_state

    def on_episode_end(self, final_reward):
        """
        Когда эпизод (планировка) закончился, делаем финальное обновление, если хотим.
        И логируем.
        """
        # финальный вызов store_transition с done=True
        self.store_transition(final_reward, new_state=None, done=True)

        self.log_file.write(f"[EPISODE_END] final_reward={final_reward}\n")

    def close(self):
        """
        Закрываем файл лога.
        """
        self.log_file.write("==== RLAgent session ends ====\n")
        self.log_file.close()
