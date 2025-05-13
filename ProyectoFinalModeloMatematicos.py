import tkinter as tk
from tkinter import ttk, messagebox
import math
import time
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Control de pausa/reanudación
is_paused = False
moving_cars = []

def toggle_pause():
    global is_paused
    is_paused = not is_paused
    pause_button.config(text="Reanudar" if is_paused else "Pausar")


# Parámetros globales de la simulación
CENTER_X = 250
CENTER_Y = 250
RADIUS = 100      # Radio de la circunferencia de la redoma
EXIT_R = 130      # Radio mayor para el punto de salida (lineal)

# Definición de ángulos para posiciones de entrada y salida  
entry_angles = {
    1: 270,  # Entrada 1: Desde el norte
    2: 90,   # Entrada 2: Desde el sur
    3: 180,  # Entrada 3: Desde el oeste
    4: 0     # Entrada 4: Desde el oriente
}
exit_angles = {
    1: 90,   # Salida 1: Hacia el sur
    2: 270,  # Salida 2: Hacia el norte
    3: 0,    # Salida 3: Hacia el oriente
    4: 180   # Salida 4: Hacia el occidente
}

# Variables para el cronómetro
simulation_start_time = None
total_simulation_time = 0

# Variables para el análisis de sensibilidad
lambda_values = []
mu_values = []
W_values = []
Wq_values = []
L_values = []
Lq_values = []

def update_stopwatch():
    """Actualiza el cronómetro mientras transcurre la simulación hasta alcanzar el tiempo teórico."""
    if simulation_start_time is None:
        return
    elapsed = time.time() - simulation_start_time
    if elapsed < total_simulation_time:
        cronometro_label.config(text=f"Cronómetro: {elapsed:.2f} s")
        root.after(10, update_stopwatch)
    else:
        cronometro_label.config(text=f"Cronómetro: {total_simulation_time:.2f} s")

def calculate_queue_metrics():
    try:
        # Obtener los datos ingresados
        lambda_rate = float(entry_lambda.get())  # Tasa de llegadas
        mu_rate = float(entry_mu.get())           # Tasa de servicio
        num_cars = int(entry_num_cars.get())      # Número de carros a simular
        selected_entry = int(entry_entry.get())     # Entrada (1–4)
        selected_exit = int(entry_exit.get())       # Salida (1–4)
        
        if selected_entry not in entry_angles or selected_exit not in exit_angles:
            raise ValueError("Seleccione una entrada y salida válidas (1-4).")
        
        # --- Cálculo de métricas (modelo M/M/C) ---
        num_servers = 4
        rho = lambda_rate / (num_servers * mu_rate)
        if rho >= 1:
            raise ValueError("El sistema está sobrecargado (ρ >= 1).")
        
        sum_terms = sum([(num_servers * rho) ** n / math.factorial(n) for n in range(num_servers)])
        P0 = 1 / (sum_terms + ((num_servers * rho) ** num_servers /
                               (math.factorial(num_servers) * (1 - rho))))
        Wq = (P0 * (num_servers * rho) ** num_servers * rho) / (math.factorial(num_servers) * (1 - rho) ** 2 * mu_rate)
        Lq = lambda_rate * Wq
        W = Wq + (1 / mu_rate)
        L = lambda_rate * W
        
        # Calcular el recorrido angular en la redoma (tiempo en redoma)  
        start_angle = entry_angles[selected_entry]
        target_angle = exit_angles[selected_exit]
        effective_start = start_angle if start_angle >= target_angle else start_angle + 360
        angular_distance = effective_start - target_angle
        if angular_distance == 0:
            angular_distance = 360
        # Se usa la fracción de la circunferencia para definir un tiempo extra (en segundos)
        time_in_redoma = angular_distance / 360.0
        
        total_time_in_system = W + time_in_redoma
        
        result_text.set(f"Utilización (ρ): {rho:.4f}\n"
                        f"Tiempo espera en cola (Wq): {Wq:.4f}\n"
                        f"Longitud cola (Lq): {Lq:.4f}\n"
                        f"Tiempo total (W): {total_time_in_system:.4f}\n"
                        f"Longitud total (L): {L:.4f}")
        
        # Guardamos el tiempo total para el cronómetro y comenzamos la simulación
        global simulation_start_time, total_simulation_time
        total_simulation_time = total_time_in_system
        simulation_start_time = time.time()
        update_stopwatch()
        
        # Simular múltiples carros
        simulate_multiple_cars(num_cars, selected_entry, selected_exit)
        
        # Realizar análisis de sensibilidad
        perform_sensitivity_analysis(lambda_rate, mu_rate)
    
    except ValueError as e:
        messagebox.showerror("Error", str(e))

def simulate_single_car(selected_entry, selected_exit, delay=0):
    """Simula el movimiento de un solo carro con un pequeño retraso."""
    root.after(delay, lambda: _move_car(selected_entry, selected_exit))

def simulate_multiple_cars(num_cars, selected_entry, selected_exit):
    """Simula el movimiento de múltiples carros en la redoma."""
    canvas.delete("all")
    
    # Dibujar redoma y etiquetas
    canvas.create_oval(CENTER_X - RADIUS, CENTER_Y - RADIUS,
                       CENTER_X + RADIUS, CENTER_Y + RADIUS,
                       outline="black", width=2)

    for i in range(1, 5):
        angle_rad = math.radians(entry_angles[i])
        ex = CENTER_X + (RADIUS + 20) * math.cos(angle_rad)
        ey = CENTER_Y + (RADIUS + 20) * math.sin(angle_rad)

        # Desplazamiento fino para evitar superposición
        if i == 3:  # Entrada oeste
            ex -= 30
            ey += 10
        elif i == 4:  # Entrada este
            ex += 30
            ey += 10

        canvas.create_text(ex, ey, text=f"Entrada {i}", fill="red", font=("Arial", 10, "bold"))

        angle_rad = math.radians(exit_angles[i])
        sx = CENTER_X + (RADIUS + 40) * math.cos(angle_rad)
        sy = CENTER_Y + (RADIUS + 40) * math.sin(angle_rad)

        if i == 3:  # Salida este
            sx += 30
            sy -= 10
        elif i == 4:  # Salida oeste
            sx -= 30
            sy -= 10

        canvas.create_text(sx, sy, text=f"Salida {i}", fill="green", font=("Arial", 10, "bold"))


    for i in range(num_cars):
        simulate_single_car(selected_entry, selected_exit, delay=i * 200)



def _move_car(selected_entry, selected_exit):
    rad_car = 8
    start_angle = entry_angles[selected_entry]
    target_angle = exit_angles[selected_exit]
    effective_start = start_angle if start_angle >= target_angle else start_angle + 360
    total_travel = effective_start - target_angle
    if total_travel == 0:
        total_travel = 360

    current_angle = start_angle
    car_x = CENTER_X + RADIUS * math.cos(math.radians(current_angle))
    car_y = CENTER_Y + RADIUS * math.sin(math.radians(current_angle))
    car = canvas.create_oval(car_x - rad_car, car_y - rad_car,
                             car_x + rad_car, car_y + rad_car, fill="blue")

    def move_in_circle(step=1):
        nonlocal current_angle, total_travel
        if is_paused:
            canvas.after(50, lambda: move_in_circle(step))
            return

        nonlocal current_angle, total_travel
        if step <= total_travel:
            angle = (effective_start - step) % 360
            new_x = CENTER_X + RADIUS * math.cos(math.radians(angle))
            new_y = CENTER_Y + RADIUS * math.sin(math.radians(angle))
            canvas.coords(car, new_x - rad_car, new_y - rad_car, new_x + rad_car, new_y + rad_car)
            canvas.after(20, lambda: move_in_circle(step + 1))
        else:
            move_to_exit()

    def move_to_exit():
        exit_x = CENTER_X + EXIT_R * math.cos(math.radians(target_angle))
        exit_y = CENTER_Y + EXIT_R * math.sin(math.radians(target_angle))

        def step():
            if is_paused:
                canvas.after(50, step)
                return

            coords = canvas.coords(car)
            cx = (coords[0] + coords[2]) / 2
            cy = (coords[1] + coords[3]) / 2
            dx = (exit_x - cx) / 10
            dy = (exit_y - cy) / 10
            canvas.move(car, dx, dy)
            if abs(cx - exit_x) > 2 or abs(cy - exit_y) > 2:
                canvas.after(20, step)

        step()

    move_in_circle()

# Variable global de pausa
is_paused = False

def pause_simulation():
    global is_paused
    is_paused = True

def resume_simulation():
    global is_paused
    is_paused = False


def perform_sensitivity_analysis(lambda_rate, mu_rate):
    """Realiza un análisis de sensibilidad para distintas tasas λ."""
    lambda_range = [lambda_rate * i for i in [0.6, 0.8, 1.0, 1.2] if lambda_rate * i < mu_rate * 4]

    sensitivity_data = []

    for lam in lambda_range:
        rho = lam / (4 * mu_rate)
        if rho >= 1:
            continue
        sum_terms = sum([(4 * rho) ** n / math.factorial(n) for n in range(4)])
        P0 = 1 / (sum_terms + ((4 * rho) ** 4 / (math.factorial(4) * (1 - rho))))
        Wq = (P0 * (4 * rho) ** 4 * rho) / (math.factorial(4) * (1 - rho) ** 2 * mu_rate)
        Lq = lam * Wq
        W = Wq + (1 / mu_rate)
        L = lam * W

        sensitivity_data.append((lam, W, Wq, L, Lq))

    plot_sensitivity_chart(sensitivity_data)

def plot_sensitivity_chart(data):
    """Grafica los valores de W, Wq, L y Lq en función de λ."""
    fig, ax = plt.subplots(figsize=(5, 3))
    lambda_vals = [x[0] for x in data]
    W_vals = [x[1] for x in data]
    Wq_vals = [x[2] for x in data]
    L_vals = [x[3] for x in data]
    Lq_vals = [x[4] for x in data]

    ax.plot(lambda_vals, W_vals, marker='o', label='W')
    ax.plot(lambda_vals, Wq_vals, marker='o', label='Wq')
    ax.plot(lambda_vals, L_vals, marker='o', label='L')
    ax.plot(lambda_vals, Lq_vals, marker='o', label='Lq')
    ax.set_xlabel('Tasa de Llegadas (λ)')
    ax.set_ylabel('Valor')
    ax.set_title('Análisis de Sensibilidad')
    ax.legend()
    ax.grid(True)

    for widget in chart_frame.winfo_children():
        widget.destroy()

    chart_canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    chart_canvas.draw()
    chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
# --- Configuración de la interfaz gráfica ---
root = tk.Tk()
root.title("Simulación M/M/C – Múltiples Carros con Análisis de Sensibilidad")

# Aseguramos que la ventana se expanda correctamente
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

main_frame = tk.Frame(root)
main_frame.grid(row=0, column=0, sticky="nsew")
main_frame.rowconfigure(1, weight=1)
main_frame.columnconfigure(1, weight=1)

# Panel de entradas (izquierda)
input_frame = tk.Frame(main_frame)
input_frame.grid(row=0, column=0, rowspan=2, sticky="nsw", padx=10, pady=10)

tk.Label(input_frame, text="Tasa de llegadas (λ):").pack(anchor="w")
entry_lambda = tk.Entry(input_frame)
entry_lambda.pack(fill="x", pady=2)

tk.Label(input_frame, text="Tasa de servicio (μ):").pack(anchor="w")
entry_mu = tk.Entry(input_frame)
entry_mu.pack(fill="x", pady=2)

tk.Label(input_frame, text="Número de carros:").pack(anchor="w")
entry_num_cars = tk.Entry(input_frame)
entry_num_cars.insert(0, "3")  # Valor por defecto
entry_num_cars.pack(fill="x", pady=2)

tk.Label(input_frame, text="Entrada (1–4):").pack(anchor="w")
entry_entry = tk.Entry(input_frame)
entry_entry.insert(0, "1")
entry_entry.pack(fill="x", pady=2)

tk.Label(input_frame, text="Salida (1–4):").pack(anchor="w")
entry_exit = tk.Entry(input_frame)
entry_exit.insert(0, "2")
entry_exit.pack(fill="x", pady=2)

calculate_button = tk.Button(input_frame, text="Calcular", command=calculate_queue_metrics)
calculate_button.pack(pady=10, fill="x")

# Botones de pausa y reanudar
pause_button = tk.Button(input_frame, text="Pausar", command=pause_simulation, bg="orange")
pause_button.pack(pady=5, fill="x")

resume_button = tk.Button(input_frame, text="Reanudar", command=resume_simulation, bg="lightgreen")
resume_button.pack(pady=5, fill="x")


# Panel de resultados y cronómetro
output_frame = tk.Frame(main_frame)
output_frame.grid(row=0, column=1, sticky="ew", padx=10)

result_text = tk.StringVar()
result_label = tk.Label(output_frame, textvariable=result_text, justify="left", font=("Arial", 10))
result_label.pack(anchor="w")

cronometro_label = tk.Label(output_frame, text="Cronómetro: 0.00 s", font=("Arial", 10, "bold"))
cronometro_label.pack(anchor="w", pady=(5, 0))

# Panel para simulación (canvas)
canvas_frame = tk.Frame(main_frame)
canvas_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
canvas_frame.rowconfigure(0, weight=1)
canvas_frame.columnconfigure(0, weight=1)

canvas = tk.Canvas(canvas_frame, bg="white")
canvas.grid(row=0, column=0, sticky="nsew")

# Panel para el gráfico de sensibilidad
chart_frame = tk.Frame(main_frame, bd=2, relief="groove")
chart_frame.grid(row=1, column=2, sticky="nsew", padx=(0, 10), pady=10)
chart_frame.rowconfigure(0, weight=1)
chart_frame.columnconfigure(0, weight=1)

# Expandir columnas adecuadamente
main_frame.columnconfigure(1, weight=3)  # simulación
main_frame.columnconfigure(2, weight=2)  # gráfico
main_frame.rowconfigure(1, weight=1)

root.geometry("1200x700")
root.mainloop()