
import wx
import psutil
import socket
import platform
import time

from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas


class SystemMonitor(wx.Frame):

    def __init__(self):
        super().__init__(
            None,
            title="System Monitoring Dashboard",
            size=(1200, 900)
        )

        # Scrollable panel
        panel = wx.ScrolledWindow(self)
        panel.SetScrollRate(10, 10)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # ===========================
        # GRAPH SECTION
        # ===========================

        self.figure = Figure(figsize=(12, 8))

        self.cpu_ax = self.figure.add_subplot(221)
        self.ram_ax = self.figure.add_subplot(222)
        self.disk_ax = self.figure.add_subplot(223)
        self.net_ax = self.figure.add_subplot(224)

        self.canvas = FigureCanvas(panel, -1, self.figure)

        main_sizer.Add(
            self.canvas,
            0,
            wx.EXPAND | wx.ALL,
            10
        )

        # ===========================
        # SYSTEM INFO SECTION
        # ===========================

        info_box = wx.StaticBox(panel, label="System Information")
        info_sizer = wx.StaticBoxSizer(info_box, wx.VERTICAL)

        self.info_text = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 250)
        )

        info_sizer.Add(
            self.info_text,
            1,
            wx.EXPAND | wx.ALL,
            5
        )

        main_sizer.Add(
            info_sizer,
            0,
            wx.EXPAND | wx.ALL,
            10
        )

        # ===========================
        # PROCESS SECTION
        # ===========================

        process_box = wx.StaticBox(
            panel,
            label="Top 10 Memory Consuming Processes"
        )

        process_sizer = wx.StaticBoxSizer(
            process_box,
            wx.VERTICAL
        )

        self.proc_text = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 250)
        )

        process_sizer.Add(
            self.proc_text,
            1,
            wx.EXPAND | wx.ALL,
            5
        )

        main_sizer.Add(
            process_sizer,
            0,
            wx.EXPAND | wx.ALL,
            10
        )

        panel.SetSizer(main_sizer)
        panel.FitInside()

        # Data storage
        self.cpu_data = []
        self.ram_data = []
        self.net_data = []

        net = psutil.net_io_counters()
        self.prev_total = (
            net.bytes_sent + net.bytes_recv
        )

        self.timer = wx.Timer(self)

        self.Bind(
            wx.EVT_TIMER,
            self.update_dashboard,
            self.timer
        )

        self.timer.Start(1000)

    def get_uptime(self):

        uptime = int(
            time.time() - psutil.boot_time()
        )

        days = uptime // 86400
        hours = (uptime % 86400) // 3600
        minutes = (uptime % 3600) // 60

        return f"{days}d {hours}h {minutes}m"

    def get_top_processes(self):

        process_list = []

        for proc in psutil.process_iter(
            ['pid', 'name', 'memory_percent']
        ):
            try:
                process_list.append(proc.info)
            except Exception:
                pass

        process_list = sorted(
            process_list,
            key=lambda x: x['memory_percent'],
            reverse=True
        )

        return process_list[:10]

    def update_dashboard(self, event):

        cpu = psutil.cpu_percent()

        ram = psutil.virtual_memory().percent

        disk = psutil.disk_usage('/').percent

        net = psutil.net_io_counters()

        current_total = (
            net.bytes_sent +
            net.bytes_recv
        )

        net_speed = (
            current_total -
            self.prev_total
        ) / 1024

        self.prev_total = current_total

        # Store historical values
        self.cpu_data.append(cpu)
        self.ram_data.append(ram)
        self.net_data.append(net_speed)

        if len(self.cpu_data) > 60:
            self.cpu_data.pop(0)
            self.ram_data.pop(0)
            self.net_data.pop(0)

        # CPU GRAPH
        self.cpu_ax.clear()
        self.cpu_ax.plot(
            self.cpu_data,
            label="CPU %"
        )
        self.cpu_ax.set_title(
            "CPU Usage (%)"
        )
        self.cpu_ax.set_ylim(0, 100)
        self.cpu_ax.legend()

        # RAM GRAPH
        self.ram_ax.clear()
        self.ram_ax.plot(
            self.ram_data,
            label="RAM %"
        )
        self.ram_ax.set_title(
            "RAM Usage (%)"
        )
        self.ram_ax.set_ylim(0, 100)
        self.ram_ax.legend()

        # DISK BAR
        self.disk_ax.clear()
        self.disk_ax.bar(
            ["Disk"],
            [disk]
        )
        self.disk_ax.set_ylim(0, 100)
        self.disk_ax.set_title(
            "Disk Usage (%)"
        )

        # NETWORK GRAPH
        self.net_ax.clear()
        self.net_ax.plot(
            self.net_data,
            label="KB/s"
        )
        self.net_ax.set_title(
            "Network Traffic"
        )
        self.net_ax.legend()

        self.figure.tight_layout()
        self.canvas.draw()

        # System Info
        hostname = socket.gethostname()

        try:
            ip = socket.gethostbyname(
                hostname
            )
        except Exception:
            ip = "Unavailable"

        memory = psutil.virtual_memory()

        info = f"""
Hostname           : {hostname}
IP Address         : {ip}

Operating System   : {platform.system()} {platform.release()}
Architecture       : {platform.machine()}
Processor          : {platform.processor()}

CPU Usage          : {cpu:.2f} %
Physical Cores     : {psutil.cpu_count(logical=False)}
Logical Cores      : {psutil.cpu_count(logical=True)}

RAM Usage          : {memory.percent:.2f} %
Total RAM          : {memory.total / (1024**3):.2f} GB
Available RAM      : {memory.available / (1024**3):.2f} GB

Disk Usage         : {disk:.2f} %

Network Speed      : {net_speed:.2f} KB/s

Running Processes  : {len(psutil.pids())}

System Uptime      : {self.get_uptime()}
"""

        self.info_text.SetValue(info)

        # Process Information
        output = ""

        for proc in self.get_top_processes():

            output += (
                f"PID: {proc['pid']}   "
                f"Name: {proc['name']}   "
                f"Memory: {proc['memory_percent']:.2f}%\n"
            )

        self.proc_text.SetValue(output)


if __name__ == "__main__":

    app = wx.App()

    frame = SystemMonitor()

    frame.Show()

    app.MainLoop()
