"""
Модуль для экспорта результатов акустических расчетов в Excel
"""
import pandas as pd
from typing import Dict, Any, List, Optional
from io import BytesIO
from datetime import datetime


def export_calculation_results_to_excel(
    room_data: Dict[str, Any],
    structural_results: Optional[Dict[str, Any]] = None,
    combined_results: Optional[Dict[str, Any]] = None,
    structural_materials: Optional[List[Dict[str, Any]]] = None,
    acoustic_materials: Optional[List[Dict[str, Any]]] = None
) -> BytesIO:
    """
    Экспорт результатов расчетов в Excel файл
    
    Args:
        room_data: Данные помещения (название, назначение, размеры, объем)
        structural_results: Результаты расчета только ограждающих конструкций
        combined_results: Результаты расчета с учетом акустических материалов
        structural_materials: Список ограждающих материалов
        acoustic_materials: Список акустических материалов
        
    Returns:
        BytesIO объект с Excel файлом
    """
    output = BytesIO()
    
    # Создание Excel файла с помощью xlsxwriter  
    with pd.ExcelWriter(output, engine='xlsxwriter', options={'remove_timezone': True}) as writer:
        workbook = writer.book
        
        # Форматы ячеек
        header_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'bg_color': '#D7E4BC',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        data_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        number_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '0.000'
        })
        
        # Лист 1: Исходные данные
        _create_input_data_sheet(writer, workbook, room_data, structural_materials, acoustic_materials, header_format, data_format)
        
        # Лист 2: Расчет ограждающих конструкций
        if structural_results:
            _create_structural_calculations_sheet(writer, workbook, structural_results, header_format, data_format, number_format)
        
        # Лист 3: Расчет с акустическими материалами
        if combined_results:
            _create_combined_calculations_sheet(writer, workbook, combined_results, header_format, data_format, number_format)
        
        # Лист 4: Сравнение результатов
        if structural_results and combined_results:
            _create_comparison_sheet(writer, workbook, structural_results, combined_results, header_format, data_format, number_format)
    
    output.seek(0)
    return output


def _create_input_data_sheet(writer, workbook, room_data, structural_materials, acoustic_materials, header_format, data_format):
    """Создание листа с исходными данными"""
    
    # Данные помещения
    room_info = [
        ['Наименование помещения', room_data.get('name', '')],
        ['Назначение помещения', room_data.get('purpose', '')],
        ['Длина (м)', room_data.get('length', 0)],
        ['Ширина (м)', room_data.get('width', 0)],
        ['Высота (м)', room_data.get('height', 0)],
        ['Объем (м³)', room_data.get('volume', 0)],
        ['Общая площадь поверхностей (м²)', room_data.get('total_surface_area', 0)],
        ['Дата расчета', datetime.now().strftime('%d.%m.%Y %H:%M')]
    ]
    
    room_df = pd.DataFrame(room_info, columns=['Параметр', 'Значение'])
    room_df.to_excel(writer, sheet_name='Исходные данные', index=False, startrow=0, startcol=0)
    
    worksheet = writer.sheets['Исходные данные']
    
    # Форматирование заголовков и данных помещения
    for row in range(len(room_info) + 1):
        for col in range(2):
            if row == 0:
                worksheet.write(row, col, room_df.columns[col], header_format)
            else:
                worksheet.write(row, col, room_info[row-1][col], data_format)
    
    # Ограждающие конструкции
    if structural_materials:
        start_row = len(room_info) + 3
        worksheet.write(start_row, 0, 'ОГРАЖДАЮЩИЕ КОНСТРУКЦИИ', header_format)
        
        structural_data = []
        for material in structural_materials:
            structural_data.append([
                material['name'],
                material['surface_type'],
                f"{material['area']:.2f}"
            ])
        
        structural_df = pd.DataFrame(structural_data, columns=['Материал', 'Тип поверхности', 'Площадь (м²)'])
        structural_df.to_excel(writer, sheet_name='Исходные данные', index=False, startrow=start_row+1, startcol=0)
        
        # Форматирование таблицы ограждающих конструкций
        for row in range(len(structural_data) + 1):
            for col in range(3):
                if row == 0:
                    worksheet.write(start_row + 1 + row, col, structural_df.columns[col], header_format)
                else:
                    worksheet.write(start_row + 1 + row, col, structural_data[row-1][col], data_format)
    
    # Акустические конструкции
    if acoustic_materials:
        start_row = len(room_info) + 3 + (len(structural_materials) + 2 if structural_materials else 0) + 2
        worksheet.write(start_row, 0, 'АКУСТИЧЕСКИЕ КОНСТРУКЦИИ', header_format)
        
        acoustic_data = []
        for material in acoustic_materials:
            acoustic_data.append([
                material['name'],
                material['surface_type'],
                f"{material['area']:.2f}"
            ])
        
        acoustic_df = pd.DataFrame(acoustic_data, columns=['Материал', 'Тип поверхности', 'Площадь (м²)'])
        acoustic_df.to_excel(writer, sheet_name='Исходные данные', index=False, startrow=start_row+1, startcol=0)
        
        # Форматирование таблицы акустических конструкций
        for row in range(len(acoustic_data) + 1):
            for col in range(3):
                if row == 0:
                    worksheet.write(start_row + 1 + row, col, acoustic_df.columns[col], header_format)
                else:
                    worksheet.write(start_row + 1 + row, col, acoustic_data[row-1][col], data_format)
    
    # Автоподбор ширины колонок
    worksheet.set_column('A:A', 25)
    worksheet.set_column('B:B', 15)
    worksheet.set_column('C:C', 15)


def _create_structural_calculations_sheet(writer, workbook, results, header_format, data_format, number_format):
    """Создание листа с расчетами ограждающих конструкций"""
    
    frequencies = [125, 250, 500, 1000, 2000, 4000]
    
    # Основные результаты
    main_data = []
    for freq in frequencies:
        main_data.append([
            freq,
            results['reverberation_times'][freq],
            results['average_absorption_coefficients'][freq],
            results['equivalent_absorption_areas'][freq],
            results['phi_values'][freq]
        ])
    
    main_df = pd.DataFrame(main_data, columns=[
        'Частота (Гц)',
        'Время реверберации (с)',
        'Средний КЗП',
        'ЭПЗ (м²)',
        'φ(αср)'
    ])
    
    main_df.to_excel(writer, sheet_name='Расчет ОК', index=False, startrow=2, startcol=0)
    
    worksheet = writer.sheets['Расчет ОК']
    
    # Заголовок листа
    worksheet.write(0, 0, 'РАСЧЕТ ВРЕМЕНИ РЕВЕРБЕРАЦИИ (ОГРАЖДАЮЩИЕ КОНСТРУКЦИИ)', header_format)
    
    # Основные параметры
    worksheet.write(1, 0, f"Критическая частота: {results['critical_frequency']:.1f} Гц", data_format)
    worksheet.write(1, 2, f"Объем помещения: {results['room_volume']:.2f} м³", data_format)
    
    # Форматирование основной таблицы
    for row in range(len(frequencies) + 1):
        for col in range(5):
            if row == 0:
                worksheet.write(2 + row, col, main_df.columns[col], header_format)
            else:
                if col == 0:  # Частота
                    worksheet.write(2 + row, col, main_data[row-1][col], data_format)
                else:  # Числовые значения
                    worksheet.write(2 + row, col, main_data[row-1][col], number_format)
    
    # Автоподбор ширины колонок
    worksheet.set_column('A:E', 18)


def _create_combined_calculations_sheet(writer, workbook, results, header_format, data_format, number_format):
    """Создание листа с расчетами с учетом акустических материалов"""
    
    frequencies = [125, 250, 500, 1000, 2000, 4000]
    
    # Основные результаты
    main_data = []
    for freq in frequencies:
        main_data.append([
            freq,
            results['reverberation_times'][freq],
            results['average_absorption_coefficients'][freq],
            results['equivalent_absorption_areas'][freq],
            results.get('structural_absorption_areas', {}).get(freq, 0),
            results.get('acoustic_absorption_areas', {}).get(freq, 0),
            results['phi_values'][freq]
        ])
    
    main_df = pd.DataFrame(main_data, columns=[
        'Частота (Гц)',
        'Время реверберации (с)',
        'Средний КЗП',
        'ЭПЗ общая (м²)',
        'ЭПЗ ОК (м²)',
        'ЭПЗ АК (м²)',
        'φ(αср)'
    ])
    
    main_df.to_excel(writer, sheet_name='Расчет с АК', index=False, startrow=2, startcol=0)
    
    worksheet = writer.sheets['Расчет с АК']
    
    # Заголовок листа
    worksheet.write(0, 0, 'РАСЧЕТ ВРЕМЕНИ РЕВЕРБЕРАЦИИ (С АКУСТИЧЕСКИМИ МАТЕРИАЛАМИ)', header_format)
    
    # Основные параметры
    worksheet.write(1, 0, f"Критическая частота: {results['critical_frequency']:.1f} Гц", data_format)
    worksheet.write(1, 2, f"Объем помещения: {results['room_volume']:.2f} м³", data_format)
    worksheet.write(1, 4, f"Эффективная площадь: {results.get('effective_surface_area', 0):.2f} м²", data_format)
    
    # Форматирование основной таблицы
    for row in range(len(frequencies) + 1):
        for col in range(7):
            if row == 0:
                worksheet.write(2 + row, col, main_df.columns[col], header_format)
            else:
                if col == 0:  # Частота
                    worksheet.write(2 + row, col, main_data[row-1][col], data_format)
                else:  # Числовые значения
                    worksheet.write(2 + row, col, main_data[row-1][col], number_format)
    
    # Автоподбор ширины колонок
    worksheet.set_column('A:G', 16)


def _create_comparison_sheet(writer, workbook, structural_results, combined_results, header_format, data_format, number_format):
    """Создание листа со сравнением результатов"""
    
    frequencies = [125, 250, 500, 1000, 2000, 4000]
    
    # Сравнение времен реверберации
    comparison_data = []
    for freq in frequencies:
        structural_time = structural_results['reverberation_times'][freq]
        combined_time = combined_results['reverberation_times'][freq]
        difference = structural_time - combined_time
        percentage = (difference / structural_time) * 100 if structural_time > 0 else 0
        
        comparison_data.append([
            freq,
            structural_time,
            combined_time,
            difference,
            percentage
        ])
    
    comparison_df = pd.DataFrame(comparison_data, columns=[
        'Частота (Гц)',
        'Время ОК (с)',
        'Время с АК (с)',
        'Разность (с)',
        'Снижение (%)'
    ])
    
    comparison_df.to_excel(writer, sheet_name='Сравнение', index=False, startrow=2, startcol=0)
    
    worksheet = writer.sheets['Сравнение']
    
    # Заголовок листа
    worksheet.write(0, 0, 'СРАВНЕНИЕ РЕЗУЛЬТАТОВ РАСЧЕТОВ', header_format)
    
    # Форматирование таблицы сравнения
    for row in range(len(frequencies) + 1):
        for col in range(5):
            if row == 0:
                worksheet.write(2 + row, col, comparison_df.columns[col], header_format)
            else:
                if col == 0:  # Частота
                    worksheet.write(2 + row, col, comparison_data[row-1][col], data_format)
                else:  # Числовые значения
                    worksheet.write(2 + row, col, comparison_data[row-1][col], number_format)
    
    # Автоподбор ширины колонок
    worksheet.set_column('A:E', 16)