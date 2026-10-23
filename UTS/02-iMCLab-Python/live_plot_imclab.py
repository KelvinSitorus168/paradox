"""
live_plot_imclab.py — grafik real-time RPM & PWM dari kit iMCLab (atau simulator),
dengan kendali PI dari Python. Setpoint bisa diubah lewat keyboard di jendela grafik:
    panah atas/bawah = setpoint ±500 RPM,  spasi = stop
    python live_plot_imclab.py --port COM5
    python live_plot_imclab.py --sim
"""
import argparse
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from pid_python_imclab import KP, TAU, THETA, PI

TS = 0.05


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", action="store_true")
    ap.add_argument("--port")
    args = ap.parse_args()
    if args.sim:
        from imclab_sim import iMCLabSim
        lab = iMCLabSim(method="period")       # encoder 2 lubang, metode period
    else:
        from imclab import iMCLab
        lab = iMCLab(args.port)

    ctrl = PI(TAU / (KP * (0.1 + THETA)), TAU)
    st = {"sp": 3000.0, "t": 0.0}
    N = 200
    T, SP, PV, U = (deque(maxlen=N) for _ in range(4))
    fig, (a1, a2) = plt.subplots(2, 1, sharex=True, figsize=(9, 6))
    l_sp, = a1.plot([], [], "k--", label="setpoint"); l_pv, = a1.plot([], [], "r", label="RPM")
    l_u, = a2.plot([], [], "b", label="PWM")
    a1.set_ylabel("RPM"); a2.set_ylabel("PWM"); a2.set_xlabel("Waktu (s)"); a1.legend(loc="upper left")

    def on_key(ev):
        if ev.key == "up": st["sp"] += 500
        elif ev.key == "down": st["sp"] = max(0, st["sp"] - 500)
        elif ev.key == " ": st["sp"] = 0
    fig.canvas.mpl_connect("key_press_event", on_key)

    def update(_):
        y = lab.rpm
        u = ctrl.update(st["sp"], y, TS) if st["sp"] > 0 else 0
        lab.pwm(round(u))
        lab.step(TS) if args.sim else None
        st["t"] += TS
        T.append(st["t"]); SP.append(st["sp"]); PV.append(y); U.append(u)
        l_sp.set_data(T, SP); l_pv.set_data(T, PV); l_u.set_data(T, U)
        for a in (a1, a2):
            a.relim(); a.autoscale_view()
        return l_sp, l_pv, l_u

    _ani = FuncAnimation(fig, update, interval=int(TS * 1000), cache_frame_data=False)
    plt.show()
    lab.close()


if __name__ == "__main__":
    main()
