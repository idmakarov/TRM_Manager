"""

This is configuration file. Its purpose is to provide other python modules
with required initialization information.

"""


def get_config():
    # Пропишем пути
    templates_dir = 'templates'
    process_dir = 'prc'
    
    # Список директорий проекта
    dir_dict = {
        'templates_dir': templates_dir,
        'process_dir': process_dir
    }
    
    # Список масок для поиска TRM и VDR
    send_trm_mask = '0055-P2-GA1-CPC-TRM*'
    received_trm_mask = '0055-P2-CPC-GA1-TRM*'
    vdr_mask = '0055-CPC-GA1-4.*.xlsx'
    mask_dict = {
        'send_trm_mask': send_trm_mask,
        'received_trm_mask': received_trm_mask,
        'vdr_mask': vdr_mask
    }
    
    # Список ревизий поставщика для пересмотра документа
    ifr_list = ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1']
    # Список ревизий поставщика для использования документа
    ifu_list = ['00', '01', '02', '03', '04', '05', '06']
    issue_dict = {
        'ifr_list': ifr_list,
        'ifu_list': ifu_list
    }

    format_dict = {
        'A0': [(33.1, 46.8)],
        'A1': [(23.4, 33.1)],
        'A2': [(16.5, 23.4)],
        'A3': [(16.2, 22.3), (11.7, 16.5)],
        'A4': [(11.2, 14.5), (8.3, 11.7), (8.5, 11.0)]
    }
    
    cfg = (dir_dict, mask_dict, issue_dict, format_dict)
    return cfg
