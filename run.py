from flask import Flask, render_template
import csv
import os

app = Flask(__name__)

def load_csv_data(filepath):
    clients = []
    try:
        with open(filepath, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if not row:
                    continue
                
                # Нормализуем значение HasOnlineTV
                has_tv = row.get('HasOnlineTV', '').strip().lower()
                if has_tv == 'no internet service':
                    continue  # Пропускаем клиентов без интернет-сервиса
                
                row['HasOnlineTV'] = '1' if has_tv == 'yes' else '0'
                
                # Преобразуем другие важные поля
                try:
                    row['Churn'] = int(row.get('Churn', 0))
                    row['MonthlySpending'] = float(row.get('MonthlySpending', 0))
                    row['ClientPeriod'] = int(row.get('ClientPeriod', 0))
                except (ValueError, TypeError):
                    continue
                
                clients.append(row)
                
        print(f"Успешно загружено {len(clients)} клиентов")
    except Exception as e:
        print(f"Ошибка при чтении файла: {str(e)}")
    return clients

def calculate_online_tv_stats(clients):
    stats = []
    if not clients:
        return stats
    
    # Группируем по наличию онлайн ТВ
    for has_tv in ['1', '0']:
        filtered_clients = [c for c in clients if c.get('HasOnlineTV') == has_tv]
        count = len(filtered_clients)
        
        if count == 0:
            continue
            
        churn_count = sum(1 for c in filtered_clients if c.get('Churn') == 1)
        churn_percent = (churn_count / count) * 100
        avg_spend = sum(float(c.get('MonthlySpending', 0)) for c in filtered_clients) / count
        
        stats.append({
            'has_online_tv': has_tv,
            'count': count,
            'churn_percent': churn_percent,
            'avg_spend': avg_spend,
            'label': 'Yes' if has_tv == '1' else 'No'  # Добавляем понятную метку
        })
    
    print(f"Статистика по TV: {stats}")
    return stats

@app.route('/')
def dashboard():
    csv_path = os.path.join(os.path.dirname(__file__), 'train.csv')
    print(f"Путь к файлу: {csv_path}")
    
    if not os.path.exists(csv_path):
        print("Файл train.csv не найден!")
        return render_template('index.html', online_tv_stats=[])
    
    clients = load_csv_data(csv_path)
    online_tv_stats = calculate_online_tv_stats(clients)
    
    # Рассчитываем максимальные значения для прогресс-баров
    max_churn = max(s['churn_percent'] for s in online_tv_stats) if online_tv_stats else 100
    max_spend = max(s['avg_spend'] for s in online_tv_stats) if online_tv_stats else 100
    
    return render_template(
        'index.html',
        online_tv_stats=online_tv_stats,
        max_churn=max_churn,
        max_spend=max_spend,
        clients=clients,
        churn_rate=sum(1 for c in clients if c.get('Churn') == 1) / len(clients) if clients else 0,
        avg_monthly_spending=sum(float(c.get('MonthlySpending', 0)) for c in clients) / len(clients) if clients else 0,
        max_period=max(int(c.get('ClientPeriod', 0)) for c in clients) if clients else 0
    )

if __name__ == '__main__':
    app.run(debug=True)