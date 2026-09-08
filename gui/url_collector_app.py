#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""粘贴商品链接即可采集的桌面窗口。"""

import os
import queue
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Dict

from collector.service import CollectionEvent, CollectionService


COLORS = {
    'background': '#F3F4F6',
    'card': '#FFFFFF',
    'text': '#172033',
    'muted': '#526173',
    'border': '#D7DEE8',
    'primary': '#C2410C',
    'primary_active': '#9A3412',
    'success': '#137A4B',
    'error': '#C62828',
    'log_bg': '#111827',
    'log_fg': '#E5E7EB',
}


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
        self.root.geometry('980x700')
        self.root.minsize(820, 600)
        self.root.configure(bg=COLORS['background'])
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

        self.url_var = tk.StringVar()
        self.platform_var = tk.StringVar(value='等待输入商品链接')
        self.status_var = tk.StringVar(value='准备就绪')
        self.stage_var = tk.StringVar(value='粘贴商品链接后开始采集')
        self.progress_var = tk.IntVar(value=0)
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
        style.configure('Card.TFrame', background=COLORS['card'])
        style.configure(
            'Heading.TLabel',
            background=COLORS['background'],
            foreground=COLORS['text'],
            font=('Microsoft YaHei UI', 20, 'bold'),
        )
        style.configure(
            'Subtitle.TLabel',
            background=COLORS['background'],
            foreground=COLORS['muted'],
            font=('Microsoft YaHei UI', 10),
        )
        style.configure(
            'CardTitle.TLabel',
            background=COLORS['card'],
            foreground=COLORS['text'],
            font=('Microsoft YaHei UI', 11, 'bold'),
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
        style.configure('Secondary.TButton', font=('Microsoft YaHei UI', 9), padding=(12, 8))
        style.configure(
            'Collector.Horizontal.TProgressbar',
            troughcolor='#E5E7EB',
            background=COLORS['primary'],
            bordercolor='#E5E7EB',
            lightcolor=COLORS['primary'],
            darkcolor=COLORS['primary'],
        )

    def _build_layout(self) -> None:
        outer = ttk.Frame(self.root, style='App.TFrame', padding=24)
        outer.pack(fill='both', expand=True)

        ttk.Label(outer, text='商品链接自动采集', style='Heading.TLabel').pack(anchor='w')
        ttk.Label(
            outer,
            text='自动识别平台、保存页面、下载素材并生成结构化数据',
            style='Subtitle.TLabel',
        ).pack(anchor='w', pady=(4, 18))

        input_card = ttk.Frame(outer, style='Card.TFrame', padding=18)
        input_card.pack(fill='x')
        input_card.columnconfigure(0, weight=1)

        ttk.Label(input_card, text='商品链接', style='CardTitle.TLabel').grid(
            row=0, column=0, sticky='w'
        )
        self.platform_label = ttk.Label(input_card, textvariable=self.platform_var, style='Muted.TLabel')
        self.platform_label.grid(row=0, column=1, sticky='e', padx=(12, 0))

        self.url_entry = ttk.Entry(input_card, textvariable=self.url_var, font=('Microsoft YaHei UI', 10))
        self.url_entry.grid(row=1, column=0, sticky='ew', pady=(10, 0), ipady=8)
        self.start_button = ttk.Button(
            input_card,
            text='开始采集',
            style='Primary.TButton',
            command=self._start_collection,
        )
        self.start_button.grid(row=1, column=1, padx=(12, 0), pady=(10, 0))

        status_row = ttk.Frame(input_card, style='Card.TFrame')
        status_row.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(16, 0))
        status_row.columnconfigure(1, weight=1)
        self.status_label = ttk.Label(status_row, textvariable=self.status_var, style='Body.TLabel')
        self.status_label.grid(row=0, column=0, sticky='w')
        ttk.Label(status_row, textvariable=self.stage_var, style='Muted.TLabel').grid(
            row=0, column=1, sticky='e', padx=(16, 0)
        )
        ttk.Progressbar(
            status_row,
            variable=self.progress_var,
            maximum=100,
            style='Collector.Horizontal.TProgressbar',
        ).grid(row=1, column=0, columnspan=2, sticky='ew', pady=(9, 0))

        content = ttk.Panedwindow(outer, orient='horizontal')
        content.pack(fill='both', expand=True, pady=(16, 0))

        log_card = ttk.Frame(content, style='Card.TFrame', padding=14)
        result_card = ttk.Frame(content, style='Card.TFrame', padding=16)
        content.add(log_card, weight=3)
        content.add(result_card, weight=2)

        ttk.Label(log_card, text='实时日志', style='CardTitle.TLabel').pack(anchor='w', pady=(0, 10))
        log_wrap = ttk.Frame(log_card, style='Card.TFrame')
        log_wrap.pack(fill='both', expand=True)
        self.log_text = tk.Text(
            log_wrap,
            bg=COLORS['log_bg'],
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
        scrollbar = ttk.Scrollbar(log_wrap, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        ttk.Label(result_card, text='采集结果', style='CardTitle.TLabel').pack(anchor='w')
        ttk.Label(
            result_card,
            textvariable=self.summary_vars['title'],
            style='Body.TLabel',
            wraplength=300,
            justify='left',
        ).pack(anchor='w', fill='x', pady=(12, 18))

        metrics = ttk.Frame(result_card, style='Card.TFrame')
        metrics.pack(fill='x')
        for index, (key, label) in enumerate((
            ('price', '起批价'),
            ('sku_count', 'SKU'),
            ('image_count', '图片'),
            ('video_count', '视频'),
        )):
            row, column = divmod(index, 2)
            cell = ttk.Frame(metrics, style='Card.TFrame', padding=(0, 5))
            cell.grid(row=row, column=column, sticky='w', pady=5)
            metrics.columnconfigure(column, weight=1)
            ttk.Label(
                cell,
                textvariable=self.summary_vars[key],
                style='CardTitle.TLabel',
            ).pack(anchor='w')
            ttk.Label(cell, text=label, style='Muted.TLabel').pack(anchor='w')

        shop_row = ttk.Frame(result_card, style='Card.TFrame')
        shop_row.pack(fill='x', pady=(14, 18))
        ttk.Label(shop_row, text='店铺', style='Muted.TLabel').pack(anchor='w')
        ttk.Label(
            shop_row,
            textvariable=self.summary_vars['shop'],
            style='Body.TLabel',
            wraplength=300,
        ).pack(anchor='w', pady=(4, 0))

        self.open_button = ttk.Button(
            result_card,
            text='打开结果目录',
            style='Secondary.TButton',
            command=self._open_output_dir,
            state='disabled',
        )
        self.open_button.pack(side='bottom', fill='x')

    def _on_url_changed(self, *_args) -> None:
        if self.service.running:
            return
        try:
            target = self.service.prepare(self.url_var.get())
            self.platform_var.set(f'已识别平台：{target.platform}')
        except ValueError as exc:
            self.platform_var.set(str(exc))

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
        self.progress_var.set(5)
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
            self.progress_var.set(event.progress)
            stage_name = event.data.get('stage', '正在采集')
            self._set_status(stage_name, event.message, COLORS['primary'])
            return
        if event.kind == 'success':
            self.progress_var.set(100)
            self._show_summary(event.data)
            self._append_log('采集完成，可以打开结果目录。')
            self._set_status('采集完成', '结果已保存', COLORS['success'])
            self._restore_controls()
            return
        if event.kind == 'cancelled':
            self._append_log(event.message)
            self._set_status('已取消', '可以重新输入链接', COLORS['muted'])
            self.progress_var.set(0)
            self._restore_controls()
            return
        if event.kind == 'error':
            self._append_log(f'错误：{event.message}')
            self._set_status('采集失败', f'{event.message}；请修正后重试', COLORS['error'])
            self._restore_controls()

    def _show_summary(self, result: Dict[str, Any]) -> None:
        summary = build_summary(result)
        for key, variable in self.summary_vars.items():
            variable.set(summary[key])
        self.output_dir = summary['output_dir']
        if self.output_dir and Path(self.output_dir).is_dir():
            self.open_button.configure(state='normal')

    def _clear_summary(self) -> None:
        self.output_dir = ''
        for variable in self.summary_vars.values():
            variable.set('—')

    def _set_status(self, status: str, detail: str, color: str) -> None:
        self.status_var.set(status)
        self.stage_var.set(detail)
        self.status_label.configure(foreground=color)

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state='normal')
        self.log_text.insert('end', message + '\n')
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
