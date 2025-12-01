import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

# Set font for Chinese characters in matplotlib
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS'] 
plt.rcParams['axes.unicode_minus'] = False

def install_and_import(package):
    import importlib
    try:
        importlib.import_module(package)
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    finally:
        globals()[package] = importlib.import_module(package)

# Try to import snownlp, fallback to simple keyword analysis if fails
try:
    from snownlp import SnowNLP
    HAS_SNOWNLP = True
    print("SnowNLP imported successfully.")
except ImportError:
    HAS_SNOWNLP = False
    print("SnowNLP not found. Using keyword-based analysis.")

def get_sentiment_score(text):
    if not isinstance(text, str):
        return 0.5
    
    if HAS_SNOWNLP:
        try:
            s = SnowNLP(text)
            return s.sentiments
        except:
            return 0.5
    else:
        # Simple keyword fallback
        positive_words = ['感動', '恭喜', '加油', '喜歡', '讚', '好棒', '感謝', '溫暖', '舒服', '鬼', '強', '贏', '冠軍', '開心', '快樂', '愛', '支持', '期待', '笑死', '好笑']
        negative_words = ['水', '爛', '輸', '失望', '滾', '罵', '討厭', '廢', '假', '無聊', '生氣', '難過', '哭', '慘']
        
        score = 0.5
        for w in positive_words:
            if w in text:
                score += 0.1
        for w in negative_words:
            if w in text:
                score -= 0.1
        return max(0.0, min(1.0, score))

def analyze_and_visualize(csv_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Reading {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    if 'Content' not in df.columns:
        print("Error: 'Content' column not found in CSV.")
        return

    print("Analyzing sentiment...")
    df['Sentiment_Score'] = df['Content'].apply(get_sentiment_score)
    
    # Categorize
    def categorize(score):
        if score > 0.6:
            return 'Positive'
        elif score < 0.4:
            return 'Negative'
        else:
            return 'Neutral'
            
    df['Sentiment_Category'] = df['Sentiment_Score'].apply(categorize)
    
    print("Generating visualizations...")
    
    # 1. Histogram of Sentiment Scores
    plt.figure(figsize=(10, 6))
    plt.hist(df['Sentiment_Score'], bins=20, color='skyblue', edgecolor='black')
    plt.title('Sentiment Score Distribution')
    plt.xlabel('Sentiment Score (0=Negative, 1=Positive)')
    plt.ylabel('Count')
    plt.grid(axis='y', alpha=0.75)
    plt.savefig(os.path.join(output_dir, 'sentiment_distribution.png'))
    plt.close()
    
    # 2. Pie Chart of Categories
    category_counts = df['Sentiment_Category'].value_counts()
    plt.figure(figsize=(8, 8))
    plt.pie(category_counts, labels=category_counts.index, autopct='%1.1f%%', startangle=140, colors=['#66b3ff','#99ff99','#ffcc99'])
    plt.title('Sentiment Categories')
    plt.savefig(os.path.join(output_dir, 'sentiment_pie_chart.png'))
    plt.close()
    
    # 3. Save analyzed data
    output_csv = os.path.join(output_dir, 'analyzed_comments.csv')
    df.to_csv(output_csv, index=False)
    print(f"Analysis complete. Results saved to {output_dir}")
    print(f"Summary:\n{category_counts}")

if __name__ == "__main__":
    csv_file = "project/tainanjosh_comments.csv"
    output_folder = "project/sentiment_analysis_results"
    analyze_and_visualize(csv_file, output_folder)
