import pandas as pd
import io
import matplotlib.pyplot as plt
from data.reverberation_standarts import REVERBERATION_STANDARDS
from room import Room

def export_calculation_results_to_excel(
    room_data,
    structural_results=None,
    combined_results=None,
    structural_materials=None,
    acoustic_materials=None
):
    """
    Экспорт данных расчета реверберации помещения в Excel.
    Возвращает объект BytesIO, готовый для скачивания в Streamlit.
    """

    output = io.BytesIO()

    # Создаем Excel через pandas
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:

            # --------------------------
            # 1. Исходные данные
            # --------------------------
            input_rows = []

            input_rows.append(["Наименование помещения", room_data.get('name', '')])
            input_rows.append(["Назначение помещения", room_data.get('purpose', '')])
            input_rows.append(["Длина (м)", room_data.get('length', '')])
            input_rows.append(["Ширина (м)", room_data.get('width', '')])
            input_rows.append(["Высота (м)", room_data.get('height', '')])
            input_rows.append(["Объем (м³)", room_data.get('volume', '')])
            input_rows.append(["Общая площадь поверхностей (м²)", room_data.get('total_surface_area', '')])

            # Добавляем материалы
            if structural_materials:
                input_rows.append([])
                input_rows.append(["Ограждающие конструкции"])
                input_rows.append(["№", "Поверхность", "Материал", "Площадь (м²)"])
                for i, mat in enumerate(structural_materials):
                    input_rows.append([i+1, mat.get('surface_type',''), mat.get('name',''), mat.get('area','')])

            if acoustic_materials:
                input_rows.append([])
                input_rows.append(["Акустические материалы"])
                input_rows.append(["№", "Поверхность", "Материал", "Площадь (м²)"])
                for i, mat in enumerate(acoustic_materials):
                    input_rows.append([i+1, mat.get('surface_type',''), mat.get('name',''), mat.get('area','')])

            df_input = pd.DataFrame(input_rows)
            df_input.to_excel(writer, sheet_name='Исходные данные', index=False, header=False)

            # --------------------------
            # 2. Расчет ОК
            # --------------------------
            if structural_results:
                _create_results_sheet(writer, structural_results, 'Расчет ОК')

            # --------------------------
            # 3. Расчет с АК
            # --------------------------
            if combined_results:
                _create_results_sheet(writer, combined_results, 'Расчет с АК')

            # --------------------------
            # 4. Сравнение
            # --------------------------
            #if structural_results and combined_results:
            #    _create_comparison_sheet(writer, structural_results, combined_results)
             
            output.seek(0)
            return output

    except Exception as e:
        raise RuntimeError(f"Ошибка при формировании Excel файла: {e}")


# --------------------------
# Вспомогательные функции
# --------------------------
def _create_results_sheet(writer, results, sheet_name):
    """
    Создание листа с расчетами реверберации.
    """
    frequencies = [125, 250, 500, 1000, 2000, 4000]
    rows = []

    for freq in frequencies:
        try:
            rt = results.get('reverberation_times', {}).get(freq, None)
            avg_alpha = results.get('average_absorption_coefficients', {}).get(freq, None)
            eq_area = results.get('equivalent_absorption_areas', {}).get(freq, None)
            phi = results.get('phi_values', {}).get(freq, None)

            row = {
                'Частота (Гц)': freq,
                'Время реверберации (с)': rt,
                'Средний КЗП': avg_alpha,
                'ЭПЗ общая (м²)': eq_area,
                'φ(αср)': phi
            }
# Если есть структурные и акустические ЭПЗ
            if 'structural_absorption_areas' in results:
                row['ЭПЗ ОК (м²)'] = results.get('structural_absorption_areas', {}).get(freq, None)
                row['ЭПЗ АК (м²)'] = results.get('acoustic_absorption_areas', {}).get(freq, None)

            rows.append(row)
        except Exception:
            continue  # пропускаем частоту при проблеме

    df = pd.DataFrame(rows)
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    def _insert_reverberation_chart(workbook, worksheet, structural_results, combined_results):
        """
        Строит график времени реверберации и вставляет в Excel.
        4 линии:
        1) Минимальное время (зеленая)
        2) Максимальное время (зеленая)
        3) Исходное время (ОК, красная)
        4) Итоговое с АК (синяя)
        """
        frequencies = [125, 250, 500, 1000, 2000, 4000]
        
        purpose=room.purpose

        standarts = REVERBERATION_STANDARDS.get(purpose,{"min":{}, "max":{}})
    
        # Берем данные
        min_times = [standarts['min'].get(f, 0) for f in frequencies]
        max_times = [standarts['max'].get(f, 0) for f in frequencies]
        structural_times = [structural_results['reverberation_times'][f] for f in frequencies]
        combined_times = [combined_results['reverberation_times'][f] for f in frequencies] if combined_results else None
    
        # Построение графика
        fig, ax = plt.subplots(figsize=(8,5))
        ax.plot(frequencies, min_times, 'g--', marker='o', label="Минимальное время")
        ax.plot(frequencies, max_times, 'g-.', marker='o', label="Максимальное время")
        ax.plot(frequencies, structural_times, 'r-o', label="Исходное время (ОК)")
        if combined_times:
            ax.plot(frequencies, combined_times, 'b-o', label="Итоговое время (с АК)")
    
        ax.set_xlabel("Частота (Гц)")
        ax.set_ylabel("Время реверберации (с)")
        ax.set_title("Время реверберации по частотам")
        ax.grid(True)
        ax.legend()
    
        # Вставка графика в Excel через BytesIO
        from io import BytesIO
        img_data = BytesIO()
        fig.savefig(img_data, format='png')
        plt.close(fig)
        img_data.seek(0)
    
        worksheet.insert_image('B2', 'reverberation_chart.png', {'image_data': img_data, 'x_scale': 1, 'y_scale':1})


#def _create_comparison_sheet(writer, structural, combined):
    """
    Создание листа с сравнением результатов.
    
    frequencies = [125, 250, 500, 1000, 2000, 4000]
    rows = []

    for freq in frequencies:
        try:
            s_time = structural.get('reverberation_times', {}).get(freq, None)
            c_time = combined.get('reverberation_times', {}).get(freq, None)
            if s_time is not None and c_time is not None:
                diff = s_time - c_time
                perc = (diff / s_time * 100) if s_time > 0 else 0
            else:
                diff = perc = None

            rows.append({
                'Частота (Гц)': freq,
                'Время ОК (с)': s_time,
                'Время с АК (с)': c_time,
                'Разность (с)': diff,
                'Снижение (%)': perc
            })
        except Exception:
            continue

    df = pd.DataFrame(rows)
    df.to_excel(writer, sheet_name='Сравнение', index=False)
    """
