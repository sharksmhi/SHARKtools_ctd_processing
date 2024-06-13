import logging
import pathlib
import tkinter as tk
import traceback
from tkinter import messagebox

import file_explorer
from ctd_processing import metadata
from file_explorer.file_explorer_logger import create_xlsx_report, fe_logger
import shark_tkinter_lib.tkinter_widgets as tkw

from . import components
from .. import events
from ..saves import SaveComponents

META_COLUMNS = metadata.get_metadata_columns()
MANUAL_META_ITEMS = ['MPROG', 'SLABO', 'ALABO', 'REFSK']
LOG_LEVELS = ['error', 'warning', 'info', 'debug']


logger = logging.getLogger(__name__)


class PageEditRaw(tk.Frame):

    def __init__(self, parent, parent_app, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        self.parent = parent
        self.parent_app = parent_app
        self._saves = SaveComponents('edit')
        self._manual_meta = {}

        self._all_packs = {}

    @property
    def user(self):
        return self.parent_app.user

    def startup(self):
        """
        :return:
        """
        self._build()
        self._add_to_save()
        self._add_events()

        sharkweb_file_path = self._sharkweb_path.get()
        if sharkweb_file_path and not pathlib.Path(sharkweb_file_path).exists():
            self._sharkweb_path.set('')


    def _add_to_save(self):
        self._saves.add_components(
            self._target_dir,
            self._sharkweb_path,
            self._lims_path,
            self._use_api,
            # self._overwrite_data,
        )
        for item in MANUAL_META_ITEMS:
            self._saves.add_components(self._manual_meta[item])
        for item in LOG_LEVELS:
            self._saves.add_components(self._report_log_levels[item])
        self._saves.load()

    def _add_events(self):
        events.subscribe('change_metadata_packs_source', self._on_change_source)
        events.subscribe('change_metadata_packs_target', self._on_change_target)
        events.subscribe('change_metadata_packs_sharkweb_path', self._on_change_sharkweb_path)
        events.subscribe('change_metadata_packs_lims_path', self._on_change_lims_path)

    def close(self):
        self._saves.save()

    def update_page(self):
        pass

    def _build(self):
        self._frame_metadata_enrichment = tk.LabelFrame(self, text='Uppdatera metadata i råfiler')
        self._frame_metadata_enrichment.grid()
        tkw.grid_configure(self)

        self._build_metadata_enrichment()

    def _build_metadata_enrichment(self):
        frame = self._frame_metadata_enrichment
        r = 0
        c = 0

        LISTBOX_TITLES = dict(title_items=dict(text='Ej valda serier',
                                               fg='red',
                                               font='Helvetica 12 bold'),
                              title_selected=dict(text='Valda serier',
                                                  fg='green',
                                                  font='Helvetica 12 bold'), )

        self._source_dir = components.DirectoryButtonText(frame,
                                                          'metadata_packs_source',
                                                          title='Välj serier från mapp',
                                                          row=r,
                                                          column=c)
        r += 1
        prop = dict(
            width=40
        )
        self._packs_listbox = tkw.ListboxSelectionWidget(frame,
                                                         title_items=LISTBOX_TITLES['title_items'],
                                                         title_selected=LISTBOX_TITLES['title_selected'],
                                                         callback=self._on_select_packs,
                                                         prop_items=prop.copy(),
                                                         prop_selected=prop.copy(),
                                                         row=r,
                                                         column=c,
                                                         columnspan=2)

        r += 1
        self._target_dir = components.DirectoryButtonText(frame, 'metadata_packs_target',
                                                          title='Spara filer till mapp',
                                                          row=r,
                                                          column=c)

        r += 1
        self._labelframe_data_source = tk.LabelFrame(frame, text='Datakällor')
        self._labelframe_data_source.grid(row=r, column=0, sticky='w', padx=10)
        self._build_data_source()

        self._labelframe_manual_meta = tk.LabelFrame(frame, text='Manuell data')
        self._labelframe_manual_meta.grid(row=r, column=1, sticky='w', padx=10)
        self._build_manual_meta()

        self._labelframe_report = tk.LabelFrame(frame, text='Val för rapport')
        self._labelframe_report.grid(row=r, column=2, sticky='w', padx=10)
        self._build_report()

        # r += 1
        # frame_ow_data = tk.Frame(frame)
        # frame_ow_data.grid(row=r, column=c, sticky='w')
        # self._boolvar_overwrite_data = tk.BooleanVar()
        # self._overwrite_data = components.Checkbutton(frame_ow_data,
        #                                               'metadata_packs_overwrite_data',
        #                                               title='Skriv över data',
        #                                               row=0,
        #                                               column=0)
        # # tk.Checkbutton(frame_ow_data, text='Skriv över data', variable=self._boolvar_overwrite_data).grid(row=0, column=0)
        # tkw.grid_configure(frame_ow_data, nr_columns=2)
        #
        r += 1
        frame_ow_files = tk.Frame(frame)
        frame_ow_files.grid(row=r, column=c, sticky='w')
        # self._boolvar_overwrite_files = tk.BooleanVar()
        # tk.Checkbutton(frame_ow_files, text='Skriv över filer', variable=self._boolvar_overwrite_files).grid(row=0, column=0)
        self._overwrite_files = components.Checkbutton(frame_ow_files,
                                                       'metadata_packs_overwrite_files',
                                                       title='Skriv över filer',
                                                       row=0,
                                                       column=0)
        tkw.grid_configure(frame_ow_files, nr_columns=2)

        r += 1
        tk.Button(frame, text='Uppdatera metadata', command=self._update_metadata).grid(row=r, column=c, sticky='w')

        tkw.grid_configure(frame, nr_rows=r + 1, nr_columns=c + 1)

    def _build_data_source(self):
        frame = self._labelframe_data_source
        r = 0
        c = 0
        frame_sharkweb = tk.Frame(frame)
        frame_sharkweb.grid(row=r, column=c, sticky='w')
        self._boolvar_sharkweb = tk.BooleanVar()
        tk.Checkbutton(frame_sharkweb, variable=self._boolvar_sharkweb).grid(row=0, column=0)
        self._sharkweb_path = components.FilePathButtonText(frame_sharkweb,
                                                            'metadata_packs_sharkweb_path',
                                                            title='Välj SHARKweb-fil',
                                                            row=0,
                                                            column=1)
        tkw.grid_configure(frame_sharkweb, nr_columns=2)

        r += 1
        frame_lims = tk.Frame(frame)
        frame_lims.grid(row=r, column=c, sticky='w')
        self._boolvar_lims = tk.BooleanVar()
        tk.Checkbutton(frame_lims, variable=self._boolvar_lims).grid(row=0, column=0)
        self._lims_path = components.FilePathButtonText(frame_lims,
                                                            'metadata_packs_lims_path',
                                                            title='Välj LIMS-fil',
                                                            row=0,
                                                            column=1)
        tkw.grid_configure(frame_lims, nr_columns=2)

        r += 1
        frame_api = tk.Frame(frame)
        frame_api.grid(row=r, column=c, sticky='w')
        self._use_api = components.Checkbutton(frame_api,
                                                      'metadata_packs_use_api',
                                                      title='Använd SHARKweb-API',
                                                      row=0,
                                                      column=0)
        tkw.grid_configure(frame_api, nr_columns=2)

        r += 1
        frame_svepa = tk.Frame(frame)
        frame_svepa.grid(row=r, column=c, sticky='w')
        self._use_svepa = components.Checkbutton(frame_svepa,
                                               'metadata_packs_use_svepa',
                                               title='Använd information från SVEPA \n(skriver INTE över data från annan källa) ',
                                               row=0,
                                               column=0)
        tkw.grid_configure(frame_svepa, nr_columns=2)

    def _build_manual_meta(self):
        layout = dict(
            padx=10,
            pady=10
        )
        frame = self._labelframe_manual_meta
        self._manual_meta = {}
        r = 0
        for r, item in enumerate(MANUAL_META_ITEMS):
            # tk.Label(frame, text=item).grid(row=r, column=0, **layout)
            # self._manual_meta_stringvars[item] = tk.StringVar()
            self._manual_meta[item] = components.LabelEntry(frame,
                                                      f'manual_meta_{item}',
                                                      title=item,
                                                      width=25,
                                                      row=r,
                                                      column=0)
            # tk.Entry(frame, textvariable=self._manual_meta_stringvars[item]).grid(row=r, column=1, **layout)
        tk.Button(frame, text='Rensa', command=self._clear_manual_meta).grid(row=r+1, column=0, columnspan=2, **layout)

    def _build_report(self):
        # layout = dict(
        #     padx=10,
        #     pady=5
        # )
        frame = self._labelframe_report
        self._report_log_levels = {}
        for r, level in enumerate(LOG_LEVELS):
            cbut = components.Checkbutton(frame,
                                   f'report_level_{level}',
                                   title=f'Inkludera nivå "{level}"',
                                   row=r,
                                   column=0,
                                   pady=2)
            cbut.set(True)
            self._report_log_levels[level] = cbut

    def _clear_manual_meta(self):
        for stvar in self._manual_meta.values():
            stvar.set('')

    def _on_change_source(self, path):
        print(f'{path=}')
        try:
            self._all_packs = file_explorer.get_packages_in_directory(path)
            self._packs_listbox.update_items(sorted(self._all_packs))
        except Exception as e:
            messagebox.showerror('Något gick fel!', f'{e}\n\n{traceback.format_exc()}')
            raise

    def _on_change_target(self, path):
        pass

    def _on_select_packs(self):
        pass

    def _on_change_sharkweb_path(self, path=None):
        self._boolvar_sharkweb.set(True)

    def _on_change_lims_path(self, path=None):
        self._boolvar_lims.set(True)

    def _get_report_filter(self) -> dict:
        filter = dict(levels=[])
        for key, value in self._report_log_levels.items():
            if value.get():
                filter['levels'].append(key)
        if not len(filter['levels']):
            return {}
        return filter

    def _update_metadata(self, event=None):
        logger.info('Updating metadata')
        sharkweb_file_path = None
        lims_file_path = None
        if self._boolvar_sharkweb.get():
            sharkweb_file_path = self._sharkweb_path.get()
            if not sharkweb_file_path:
                msg = 'Ingen sharkweb-fil vald'
                logger.warning(msg)
                messagebox.showwarning('Använd sharkweb-fil', msg)
                return
            logger.info(f'Updating metadata from {sharkweb_file_path=}')

        if self._boolvar_lims.get():
            lims_file_path = self._lims_path.get()
            if not lims_file_path:
                msg = 'Ingen LIMS-file vald'
                logger.warning(msg)
                messagebox.showwarning('Använd LIMS-fil', msg)
                return
            logger.info(f'Updating metadata from {lims_file_path=}')

        output_dir = self._target_dir.get()
        if not output_dir:
            msg = 'Ingen mapp att spara till vald'
            logger.warning(msg)
            messagebox.showwarning('Uppdatera metadata', msg)
            return

        manual_meta = {}
        for item, entry in self._manual_meta.items():
            value = entry.get().strip()
            if not value:
                continue
            manual_meta[item] = value

        packs = [self._all_packs[key] for key in self._packs_listbox.get_selected()]
        if not packs:
            msg = 'Inga filer valda'
            logger.warning(msg)
            messagebox.showwarning('Uppdatera metadata', msg)
            return
        try:
            file_explorer.edit_seabird_raw_files_in_packages(
                packs=packs,
                output_dir=output_dir,
                sharkweb_api=self._use_api.get(),
                sharkweb_file_path=sharkweb_file_path,
                lims_file_path=lims_file_path,
                overwrite_files=self._overwrite_files.get(),
                from_svepa=self._use_svepa.get(),
                **manual_meta
                # columns=META_COLUMNS,
            )
            create_xlsx_report(fe_logger, open_file=True, include_items=True, filter=self._get_report_filter())
            msg = f'Metadata har lagts till i {len(packs)} profiler.'
            logger.info(msg)
            messagebox.showinfo('Uppdatera metadata', msg)
        except Exception:
            msg = traceback.format_exc()
            logger.critical(msg)
            messagebox.showerror('Uppdatera metadata', msg)
            raise

