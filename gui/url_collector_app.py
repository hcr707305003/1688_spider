#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""粘贴商品链接即可采集的桌面窗口。"""

import os
import queue
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Dict

from collector.service import CollectionEvent, CollectionService


COLORS = {
    'background': '#F4F6FA',
    'card': '#FFFFFF',
    'text': '#172033',
    'muted': '#667085',
    'subtle': '#98A2B3',
    'border': '#DFE5EC',
    'border_strong': '#C9D3E0',
    'primary': '#C2410C',
    'primary_active': '#9A3412',
    'primary_soft': '#FFF1E8',
    'success': '#167451',
    'success_soft': '#EAF8F1',
    'warning': '#A96400',
    'warning_soft': '#FFF6DC',
    'error': '#C43232',
    'error_soft': '#FDECEC',
    'neutral_soft': '#EEF2F6',
    'log_bg': '#111827',
    'log_panel': '#0B1220',
    'log_fg': '#DCE4EF',
    'log_muted': '#8190A5',
    'metric': '#F5F7FA',
}


def classify_log_level(message: str) -> str:
    """Return a stable semantic level for one GUI log line."""
    normalized = message.casefold()
    if any(marker in normalized for marker in ('[error]', '错误', '失败', '异常', 'traceback')):
        return 'error'
    if any(marker in normalized for marker in ('[warning]', '[warn]', '警告', '备用', 'fallback')):
        return 'warning'
    if any(marker in normalized for marker in (
        '[success]', '采集完成', '下载完成', '生成完成', '保存完成', '成功'
    )):
        return 'success'
    if any(marker in normalized for marker in ('[info]', '正在', '准备', '开始', '处理中', '下载')):
        return 'active'
    return 'default'


def app_icon_path() -> Path:
    """Locate the window icon in source and PyInstaller builds."""
    runtime_root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    return runtime_root / 'assets' / 'app-icon.ico'


def build_summary(result: Dict[str, Any]) -> Dict[str, str]:
    """把完整采集结果转换为稳定的 GUI 展示字段。"""
    price = result.get('price') or {}
    main_price = price.get('main_price') or {}
    price_value = main_price.get('price')
    price_text = f'¥{price_value:.2f}' if isinstance(price_value, (int, float)) else '未获取'

    downloaded = result.get('downloaded_files') or {}
    counts = downloaded.get('counts') or {}
    image_count = sum(int(counts.get(name, 0) or 0) for name in (
        'main_images', 'color_images', 'detail_images'
    ))
    shop = result.get('shop_info') or {}

    return {
        'title': result.get('title') or '未获取商品标题',
        'price': price_text,
        'sku_count': str(len(result.get('sku_matrix') or [])),
        'image_count': str(image_count),
        'video_count': str(int(counts.get('videos', 0) or 0)),
        'shop': shop.get('shop_name') or '未获取',
        'output_dir': result.get('output_dir') or '',
    }


class CollectorGUI:
    POLL_INTERVAL_MS = 100

    def __init__(self, root: tk.Tk, service: CollectionService | None = None):
        self.root = root
        self.service = service or CollectionService()
        self.output_dir = ''

        self.root.title('商品链接自动采集工具')
        try:
            self.root.iconbitmap(default=str(app_icon_path()))
        except tk.TclError:
            pass
        self.root.geometry('1040x740')
        self.root.minsize(880, 620)
        self.root.configure(bg=COLORS['background'])
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

        self.url_var = tk.StringVar()
        self.platform_var = tk.StringVar(value='等待识别')
        self.status_var = tk.StringVar(value='准备就绪')
        self.stage_var = tk.StringVar(value='粘贴商品链接后开始采集')
        self.progress_var = tk.IntVar(value=0)
        self.progress_text_var = tk.StringVar(value='0%')
        self.result_state_var = tk.StringVar(value='等待数据')
        self.summary_vars = {
            name: tk.StringVar(value='—')
            for name in ('title', 'price', 'sku_count', 'image_count', 'video_count', 'shop')
        }

        self._configure_styles()
        self._build_layout()
        self.url_var.trace_add('write', self._on_url_changed)
        self.root.bind('<Return>', self._on_enter)
        self.root.after(self.POLL_INTERVAL_MS, self._poll_events)
        self.url_entry.focus_set()

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        style.configure('App.TFrame', background=COLORS['background'])
        style.configure(
            'Card.TFrame',
            background=COLORS['card'],
            bordercolor=COLORS['border'],
            borderwidth=1,
            relief='solid',
        )
        style.configure('CardBody.TFrame', background=COLORS['card'])
        style.configure('Metric.TFrame', background=COLORS['metric'])
        style.configure('PriceMetric.TFrame', background=COLORS['primary_soft'])
        style.configure('LogCard.TFrame', background=COLORS['log_bg'])
        style.configure(
            'Heading.TLabel',
            background=COLORS['background'],
            foreground=COLORS['text'],
            font=('Microsoft YaHei UI', 22, 'bold'),
        )
        style.configure(
            'Subtitle.TLabel',
            background=COLORS['background'],
            foreground=COLORS['muted'],
            font=('Microsoft YaHei UI', 10),
        )
        style.configure(
            'Brand.TLabel',
            background=COLORS['primary_soft'],
            foreground=COLORS['primary'],
            font=('Microsoft YaHei UI', 9, 'bold'),
            padding=(10, 5),
        )
        style.configure(
            'CardTitle.TLabel',
            background=COLORS['card'],
            foreground=COLORS['text'],
            font=('Microsoft YaHei UI', 11, 'bold'),
        )
        style.configure(
            'ProductTitle.TLabel',
            background=COLORS['card'],
            foreground=COLORS['text'],
            font=('Microsoft YaHei UI', 12, 'bold'),
        )
        style.configure(
            'Body.TLabel',
            background=COLORS['card'],
            foreground=COLORS['text'],
            font=('Microsoft YaHei UI', 10),
        )
        style.configure(
            'Muted.TLabel',
            background=COLORS['card'],
            foreground=COLORS['muted'],
            font=('Microsoft YaHei UI', 9),
        )
        style.configure(
            'ShopValue.TLabel',
            background=COLORS['card'],
            foreground=COLORS['text'],
            font=('Microsoft YaHei UI', 8),
        )
        style.configure(
            'Platform.TLabel',
            background=COLORS['neutral_soft'],
            foreground=COLORS['muted'],
            font=('Microsoft YaHei UI', 9, 'bold'),
            padding=(10, 5),
        )
        style.configure(
            'PlatformSuccess.TLabel',
            background=COLORS['primary_soft'],
            foreground=COLORS['primary'],
            font=('Microsoft YaHei UI', 9, 'bold'),
            padding=(10, 5),
        )
        style.configure(
            'PlatformError.TLabel',
            background=COLORS['error_soft'],
            foreground=COLORS['error'],
            font=('Microsoft YaHei UI', 9, 'bold'),
            padding=(10, 5),
        )
        style.configure(
            'Input.TEntry',
            fieldbackground=COLORS['card'],
            foreground=COLORS['text'],
            bordercolor=COLORS['border_strong'],
            lightcolor=COLORS['border_strong'],
            darkcolor=COLORS['border_strong'],
            insertcolor=COLORS['text'],
            padding=(10, 9),
        )
        style.map(
            'Input.TEntry',
            bordercolor=[('focus', COLORS['primary'])],
            lightcolor=[('focus', COLORS['primary'])],
            darkcolor=[('focus', COLORS['primary'])],
        )
        style.configure(
            'Primary.TButton',
            background=COLORS['primary'],
            foreground='#FFFFFF',
            borderwidth=0,
            focusthickness=3,
            focuscolor='#7C2D12',
            font=('Microsoft YaHei UI', 10, 'bold'),
            padding=(22, 11),
        )
        style.map(
            'Primary.TButton',
            background=[('active', COLORS['primary_active']), ('disabled', '#C6CBD2')],
            foreground=[('disabled', '#667085')],
        )
        style.configure(
            'Secondary.TButton',
            background=COLORS['neutral_soft'],
            foreground=COLORS['text'],
            bordercolor=COLORS['border'],
            font=('Microsoft YaHei UI', 9, 'bold'),
            padding=(12, 9),
        )
        style.map(
            'Secondary.TButton',
            background=[('active', '#E2E8F0'), ('disabled', '#F3F4F6')],
            foreground=[('disabled', COLORS['subtle'])],
        )
        style.configure(
            'MetricValue.TLabel',
            background=COLORS['metric'],
            foreground=COLORS['text'],
            font=('Microsoft YaHei UI', 12, 'bold'),
        )
        style.configure(
            'MetricLabel.TLabel',
            background=COLORS['metric'],
            foreground=COLORS['muted'],
            font=('Microsoft YaHei UI', 8),
        )
        style.configure(
            'PriceValue.TLabel',
            background=COLORS['primary_soft'],
            foreground=COLORS['primary'],
            font=('Microsoft YaHei UI', 12, 'bold'),
        )
        style.configure(
            'PriceLabel.TLabel',
            background=COLORS['primary_soft'],
            foreground=COLORS['primary'],
            font=('Microsoft YaHei UI', 8),
        )
        style.configure(
            'LogTitle.TLabel',
            background=COLORS['log_bg'],
            foreground='#FFFFFF',
            font=('Microsoft YaHei UI', 11, 'bold'),
        )
        style.configure(
            'LogMeta.TLabel',
            background=COLORS['log_bg'],
            foreground=COLORS['log_muted'],
            font=('Microsoft YaHei UI', 8),
        )
        style.configure(
            'Collector.Horizontal.TProgressbar',
            troughcolor=COLORS['neutral_soft'],
            background=COLORS['primary'],
            bordercolor=COLORS['neutral_soft'],
            lightcolor=COLORS['primary'],
            darkcolor=COLORS['primary'],
            thickness=7,
        )

    def _build_layout(self) -> None:
        outer = ttk.Frame(self.root, style='App.TFrame', padding=(28, 24, 28, 26))
        outer.pack(fill='both', expand=True)

        header = ttk.Frame(outer, style='App.TFrame')
        header.pack(fill='x', pady=(0, 16))
        header.columnconfigure(0, weight=1)
        title_wrap = ttk.Frame(header, style='App.TFrame')
        title_wrap.grid(row=0, column=0, sticky='w')
        title_line = ttk.Frame(title_wrap, style='App.TFrame')
        title_line.pack(anchor='w')
        ttk.Label(title_line, text='1688 SPIDER', style='Brand.TLabel').pack(side='left')
        ttk.Label(title_line, text='商品链接自动采集', style='Heading.TLabel').pack(
            side='left', padx=(12, 0)
        )
        ttk.Label(
            title_wrap,
            text='从商品链接到完整素材与结构化数据，一步完成',
            style='Subtitle.TLabel',
        ).pack(anchor='w', pady=(6, 0))
        self.header_status_label = tk.Label(
            header,
            textvariable=self.status_var,
            bg=COLORS['success_soft'],
            fg=COLORS['success'],
            font=('Microsoft YaHei UI', 9, 'bold'),
            padx=12,
            pady=7,
        )
        self.header_status_label.grid(row=0, column=1, sticky='ne', pady=(2, 0))

        input_card = ttk.Frame(outer, style='Card.TFrame', padding=(20, 14))
        input_card.pack(fill='x')
        input_card.columnconfigure(0, weight=1)

        ttk.Label(input_card, text='商品链接', style='CardTitle.TLabel').grid(
            row=0, column=0, sticky='w'
        )
        self.platform_label = ttk.Label(
            input_card,
            textvariable=self.platform_var,
            style='Platform.TLabel',
        )
        self.platform_label.grid(row=0, column=1, sticky='e', padx=(12, 0))

        self.url_entry = ttk.Entry(
            input_card,
            textvariable=self.url_var,
            style='Input.TEntry',
            font=('Microsoft YaHei UI', 10),
        )
        self.url_entry.grid(row=1, column=0, sticky='ew', pady=(9, 0))
        self.start_button = ttk.Button(
            input_card,
            text='开始采集',
            style='Primary.TButton',
            command=self._start_collection,
        )
        self.start_button.grid(row=1, column=1, padx=(12, 0), pady=(9, 0))

        status_row = ttk.Frame(input_card, style='CardBody.TFrame')
        status_row.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(12, 0))
        status_row.columnconfigure(1, weight=1)
        self.status_label = ttk.Label(status_row, textvariable=self.status_var, style='Body.TLabel')
        self.status_label.grid(row=0, column=0, sticky='w')
        ttk.Label(status_row, textvariable=self.stage_var, style='Muted.TLabel').grid(
            row=0, column=1, sticky='e', padx=(16, 0)
        )
        ttk.Label(status_row, textvariable=self.progress_text_var, style='Muted.TLabel').grid(
            row=0, column=2, sticky='e', padx=(12, 0)
        )
        ttk.Progressbar(
            status_row,
            variable=self.progress_var,
            maximum=100,
            style='Collector.Horizontal.TProgressbar',
        ).grid(row=1, column=0, columnspan=3, sticky='ew', pady=(7, 0))

        content = ttk.Panedwindow(outer, orient='horizontal')
        content.pack(fill='both', expand=True, pady=(16, 0))

        log_card = ttk.Frame(content, style='LogCard.TFrame', padding=(16, 14))
        result_card = ttk.Frame(content, style='Card.TFrame', padding=(18, 16))
        content.add(log_card, weight=13)
        content.add(result_card, weight=7)

        log_header = ttk.Frame(log_card, style='LogCard.TFrame')
        log_header.pack(fill='x', pady=(0, 11))
        ttk.Label(log_header, text='实时日志', style='LogTitle.TLabel').pack(side='left')
        ttk.Label(log_header, text='自动滚动 · UTF-8', style='LogMeta.TLabel').pack(side='right')
        log_wrap = ttk.Frame(log_card, style='LogCard.TFrame')
        log_wrap.pack(fill='both', expand=True)
        self.log_text = tk.Text(
            log_wrap,
            bg=COLORS['log_panel'],
            fg=COLORS['log_fg'],
            insertbackground='#FFFFFF',
            selectbackground='#374151',
            relief='flat',
            wrap='word',
            font=('Consolas', 9),
            padx=12,
            pady=10,
            state='disabled',
        )
        self.log_text.tag_configure('default', foreground=COLORS['log_fg'])
        self.log_text.tag_configure('active', foreground='#F6C177')
        self.log_text.tag_configure('success', foreground='#72D6A5')
        self.log_text.tag_configure('warning', foreground='#F4C95D')
        self.log_text.tag_configure('error', foreground='#FF8585')
        scrollbar = ttk.Scrollbar(log_wrap, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        result_header = ttk.Frame(result_card, style='CardBody.TFrame')
        result_header.pack(fill='x')
        ttk.Label(result_header, text='采集结果', style='CardTitle.TLabel').pack(side='left')
        self.result_state_label = tk.Label(
            result_header,
            textvariable=self.result_state_var,
            bg=COLORS['neutral_soft'],
            fg=COLORS['muted'],
            font=('Microsoft YaHei UI', 8, 'bold'),
            padx=8,
            pady=4,
        )
        self.result_state_label.pack(side='right')
        self.open_button = ttk.Button(
            result_card,
            text='打开结果目录',
            style='Secondary.TButton',
            command=self._open_output_dir,
            state='disabled',
        )
        self.open_button.pack(side='bottom', fill='x')
        ttk.Label(
            result_card,
            textvariable=self.summary_vars['title'],
            style='ProductTitle.TLabel',
            wraplength=190,
            justify='left',
        ).pack(anchor='w', fill='x', pady=(8, 5))

        metrics = ttk.Frame(result_card, style='CardBody.TFrame')
        metrics.pack(fill='x')
        for index, (key, label) in enumerate((
            ('price', '起批价'),
            ('sku_count', 'SKU'),
            ('image_count', '图片'),
            ('video_count', '视频'),
        )):
            row, column = divmod(index, 2)
            is_price = key == 'price'
            cell = ttk.Frame(
                metrics,
                style='PriceMetric.TFrame' if is_price else 'Metric.TFrame',
                padding=(10, 1),
            )
            cell.grid(
                row=row,
                column=column,
                sticky='ew',
                padx=(0, 5) if column == 0 else (5, 0),
                pady=2,
            )
            metrics.columnconfigure(column, weight=1)
            ttk.Label(
                cell,
                textvariable=self.summary_vars[key],
                style='PriceValue.TLabel' if is_price else 'MetricValue.TLabel',
            ).pack(anchor='w')
            ttk.Label(
                cell,
                text=label,
                style='PriceLabel.TLabel' if is_price else 'MetricLabel.TLabel',
            ).pack(anchor='w')

        shop_row = ttk.Frame(result_card, style='CardBody.TFrame')
        shop_row.pack(fill='x', pady=(2, 0))
        ttk.Label(shop_row, text='店铺', style='Muted.TLabel').pack(side='left')
        ttk.Label(
            shop_row,
            textvariable=self.summary_vars['shop'],
            style='ShopValue.TLabel',
            wraplength=135,
        ).pack(side='left', padx=(8, 0))
        self._clear_summary()

    def _on_url_changed(self, *_args) -> None:
        if self.service.running:
            return
        if not self.url_var.get().strip():
            self.platform_var.set('等待识别')
            self.platform_label.configure(style='Platform.TLabel')
            return
        try:
            target = self.service.prepare(self.url_var.get())
            self.platform_var.set(f'已识别 · {target.platform}')
            self.platform_label.configure(style='PlatformSuccess.TLabel')
        except ValueError as exc:
            self.platform_var.set(str(exc))
            self.platform_label.configure(style='PlatformError.TLabel')

    def _on_enter(self, _event=None):
        if not self.service.running:
            self._start_collection()
        return 'break'

    def _start_collection(self) -> None:
        try:
            target = self.service.start(self.url_var.get())
        except (ValueError, RuntimeError) as exc:
            self._set_status('链接有误', str(exc), COLORS['error'])
            self.url_entry.focus_set()
            return

        self._clear_summary()
        self._clear_log()
        self._append_log(f'准备采集 {target.normalized_url}')
        self.url_entry.configure(state='disabled')
        self.start_button.configure(state='disabled')
        self.open_button.configure(state='disabled')
        self._set_progress(5)
        self._set_status('正在采集', f'平台：{target.platform}', COLORS['primary'])

    def _poll_events(self) -> None:
        while True:
            try:
                event = self.service.events.get_nowait()
            except queue.Empty:
                break
            self._handle_event(event)
        self.root.after(self.POLL_INTERVAL_MS, self._poll_events)

    def _handle_event(self, event: CollectionEvent) -> None:
        if event.kind == 'log':
            if event.message:
                self._append_log(event.message)
            return
        if event.kind in {'started', 'stage'}:
            self._set_progress(event.progress)
            stage_name = event.data.get('stage', '正在采集')
            self._set_status(stage_name, event.message, COLORS['primary'])
            return
        if event.kind == 'success':
            self._set_progress(100)
            self._show_summary(event.data)
            self._append_log('采集完成，可以打开结果目录。')
            self._set_status('采集完成', '结果已保存', COLORS['success'])
            self._restore_controls()
            return
        if event.kind == 'cancelled':
            self._append_log(event.message)
            self._set_status('已取消', '可以重新输入链接', COLORS['muted'])
            self._set_progress(0)
            self._set_result_state('已取消', COLORS['muted'], COLORS['neutral_soft'])
            self._restore_controls()
            return
        if event.kind == 'error':
            self._append_log(f'错误：{event.message}')
            self._set_status('采集失败', f'{event.message}；请修正后重试', COLORS['error'])
            self._set_progress(0)
            self._set_result_state('未完成', COLORS['error'], COLORS['error_soft'])
            self._restore_controls()

    def _show_summary(self, result: Dict[str, Any]) -> None:
        summary = build_summary(result)
        for key, variable in self.summary_vars.items():
            variable.set(summary[key])
        self.output_dir = summary['output_dir']
        self._set_result_state('已完成', COLORS['success'], COLORS['success_soft'])
        if self.output_dir and Path(self.output_dir).is_dir():
            self.open_button.configure(state='normal')

    def _clear_summary(self) -> None:
        self.output_dir = ''
        for key, variable in self.summary_vars.items():
            variable.set('采集完成后将在这里显示商品信息' if key == 'title' else '—')
        self._set_result_state('等待数据', COLORS['muted'], COLORS['neutral_soft'])

    def _set_status(self, status: str, detail: str, color: str) -> None:
        self.status_var.set(status)
        self.stage_var.set(detail)
        self.status_label.configure(foreground=color)
        if color == COLORS['success']:
            background = COLORS['success_soft']
        elif color == COLORS['error']:
            background = COLORS['error_soft']
        elif color == COLORS['primary']:
            background = COLORS['primary_soft']
        else:
            background = COLORS['neutral_soft']
        self.header_status_label.configure(fg=color, bg=background)

    def _set_progress(self, value: int) -> None:
        value = max(0, min(100, int(value)))
        self.progress_var.set(value)
        self.progress_text_var.set(f'{value}%')

    def _set_result_state(self, text: str, foreground: str, background: str) -> None:
        self.result_state_var.set(text)
        self.result_state_label.configure(fg=foreground, bg=background)

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state='normal')
        self.log_text.insert('end', message + '\n', (classify_log_level(message),))
        self.log_text.see('end')
        self.log_text.configure(state='disabled')

    def _clear_log(self) -> None:
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.configure(state='disabled')

    def _restore_controls(self) -> None:
        self.url_entry.configure(state='normal')
        self.start_button.configure(state='normal')
        self.url_entry.focus_set()

    def _open_output_dir(self) -> None:
        if self.output_dir and Path(self.output_dir).is_dir():
            os.startfile(self.output_dir)
        else:
            messagebox.showerror('目录不存在', '采集结果目录不存在，请重新采集。')

    def _on_close(self) -> None:
        if self.service.running:
            confirmed = messagebox.askyesno(
                '采集仍在运行',
                '关闭窗口会终止当前采集，确定要关闭吗？',
            )
            if not confirmed:
                return
            self.service.cancel()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    CollectorGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
