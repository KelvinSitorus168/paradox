"""pid_controller.py — PID diskrit (bentuk Kc, tauI, tauD) seperti di ebook,
dengan derivative-on-measurement dan anti-reset windup."""


class PID:
    def __init__(self, Kc, tauI, tauD, oplo=0.0, ophi=100.0):
        self.Kc, self.tauI, self.tauD = Kc, tauI, tauD
        self.oplo, self.ophi = oplo, ophi
        self.ierr = 0.0
        self.pv_last = None

    def update(self, sp, pv, dt):
        if self.pv_last is None:
            self.pv_last = pv
        KP = self.Kc
        KI = self.Kc / self.tauI if self.tauI > 0 else 0.0
        KD = self.Kc * self.tauD
        e = sp - pv
        self.ierr += KI * e * dt
        dpv = (pv - self.pv_last) / dt
        P, I, D = KP * e, self.ierr, -KD * dpv
        op = P + I + D
        if op < self.oplo or op > self.ophi:          # anti-reset windup
            self.ierr -= KI * e * dt
            op = min(max(op, self.oplo), self.ophi)
        self.pv_last = pv
        return op, P, self.ierr, D
