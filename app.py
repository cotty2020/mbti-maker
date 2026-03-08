
import streamlit as st
import google.generativeai as genai
import urllib.parse

# 1. APIキーの設定
# ローカルでは secrets.toml、ネット公開後は Streamlit Cloud の Secrets を自動で見に行きます
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 2. ページ設定
st.set_page_config(page_title="16タイプ性格変換", page_icon="✨")

# --- ダークモード用カスタムデザイン ---
st.markdown("""
    <style>
    /* GitHubリンクやメニューを隠す */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
     
            /* ヘッダー・フッター・ツールバーを根こそぎ消す */
    header, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] {
        visibility: hidden !important;
        height: 0 !important;
        display: none !important;
    }
            /* 右下の「Manage App」ボタンやGitHubへのリンクが含まれる要素を強制抹消 */
button[data-testid="stManageAppButton"],
.stAppDeployButton,
a[href*="kishinabeaya"] {
    display: none !important;
}
   
    
    /* 背景をダークグレーに、文字を白に固定 */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    
    /* 入力欄やボックスのラベルの色を調整 */
    label {
        color: #FFFD !important;
        font-weight: bold;
    }
    
    /* 成功メッセージ(結果)の背景色を少し濃く */
    .stAlert {
        background-color: #1E2E3E;
        color: #FFFFFF;
        border: 1px solid #4B9CD3;
    }
            


             /* 2. ボタンを特定して、あらゆる状態の色を固定 */
    div.stButton > button, 
    div.stButton > button:first-child,
    div.stButton > button:disabled,
    div.stButton > button[kind="secondary"] {
        background-color: #00E676;
        color: #000000;
        border: none !important;
        /* ここから下はデザイン */
        border-radius: 25px !important;
        height: 3.5em !important;
        width: 100% !important;
        font-weight: bold !important;
        font-size: 1.2rem !important;
        box-shadow: 0 4px 15px rgba(255, 179, 0, 0.4) !important;
    
    }

    /* マウスを乗せたとき（ホバー）の設定 */
    div.stButton > button:hover {
        background-color: #FFD54F; /* さらに明るい黄色に */
        color: #000000;
        transform: translateY(-2px); /* 少し浮き上がる演出 */
        box-shadow: 0 6px 20px rgba(255, 179, 0, 0.5);
    }
    
    /* クリックしたときの設定 */
    div.stButton > button:active {
        transform: translateY(0px);
    }
            
    </style>
    """, unsafe_allow_html=True)

# 3. モデル準備 (キャッシュして高速化)
@st.cache_resource
def get_model():
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            return genai.GenerativeModel(m.name)
    return None

model = get_model()

# 4. データ
mbti_data = {
    "INTJ (建築家)": {"icon": "🧠", "desc": "冷静沈着で論理的、効率と戦略を重視する。少し皮肉屋で知的な口調。", "info": "完璧主義で、常に最善の戦略を練るタイプです。"},
    "INTP (論理学者)": {"icon": "🧪", "desc": "独自の理論を展開し、分析的。哲学的な問いかけを含む、少し難解で独創的な口調。", "info": "客観的な分析と新しいアイデアを好む知的好奇心の塊です。"},
    "ENTJ (指揮官)": {"icon": "⚔️", "desc": "自信に満ち、目標達成への情熱が溢れる。決断力があり、リーダーシップを感じさせる強気な口調。", "info": "目標達成のために周囲を率いる、生まれながらのリーダーです。"},
    "ENTP (討論者)": {"icon": "🗣️", "desc": "好奇心旺盛で、常識を疑う。ユーモアとウィットに富んだ、相手を揺さぶるような挑戦的な口調。", "info": "頭の回転が速く、あえて反対意見をぶつけて議論を楽しむ知性派です。"},
    "INFJ (提唱者)": {"icon": "🔮", "desc": "深い洞察力と理想を持ち、静かで神秘的。他者の心に寄り添うような、詩的で慈愛に満ちた口調。", "info": "他人の感情を敏感に察知し、理想の世界を静かに追求します。"},
    "INFP (仲介者)": {"icon": "🍄", "desc": "内省的で感受性豊か。幻想的な比喩を使い、自分の心に潜るような優しい日記風。", "info": "独自の価値観を持ち、繊細な美しさと心の調和を愛します。"},
    "ENFJ (主人公)": {"icon": "🌟", "desc": "情熱的で利他的。周囲を励まし、理想の世界を熱く語る、明るく希望に満ちた口調。", "info": "カリスマ性があり、人々を良い方向へ導こうと尽力します。"},
    "ENFP (運動家)": {"icon": "🎈", "desc": "自由奔放で創造的。感情が豊かで、ワクワクするような感嘆符多めのエネルギッシュな口調。", "info": "無限の可能性を信じ、新しいことへ飛び込む自由な精神の持ち主です。"},
    "ISTJ (管理者)": {"icon": "📋", "desc": "誠実で実務的、ルールと伝統を重んじる。事実を正確に伝える、きっちりとした丁寧な口調。", "info": "規則を正しく守り、責任感を持って任務を遂行する実直なタイプです。"},
    "ISFJ (擁護者)": {"icon": "🛡️", "desc": "献身的で控えめ。日常の些細な幸せを大切にする、温かくて謙虚な「お母さん」のような口調。", "info": "縁の下の力持ちとして、周囲の人の生活を支える優しい心の持ち主です。"},
    "ESTJ (幹事)": {"icon": "📢", "desc": "現実的で秩序を重んじる。テキパキと指示を出し、社会の常識を説くような、はっきりした口調。", "info": "秩序とルールを重んじ、組織を効率よく運営するのが得意です。"},
    "ESFJ (領事)": {"icon": "🤝", "desc": "社交的で世話好き。コミュニティの調和を愛し、絵文字多めで親しみやすい、お節介だけど温かい口調。", "info": "周囲との調和を何より大切にし、みんなを喜ばせるのが大好きです。"},
    "ISTP (巨匠)": {"icon": "🛠️", "desc": "冷静で器用、今この瞬間に集中する。言葉数は少なく、事実だけをクールに述べる、職人気質な口調。", "info": "観察力に優れ、論理的な思考と柔軟な対応で問題を解決します。"},
    "ISFP (冒険家)": {"icon": "🎨", "desc": "芸術的で感受性が鋭く、自由を愛する。感覚的な表現を使い、今を感じるままに綴る、控えめながらも色彩豊かな口調。", "info": "今この瞬間を楽しみ、自分らしい美しさを形にする芸術家肌です。"},
    "ESTP (起業家)": {"icon": "🏎️", "desc": "行動力バツグンでスリルを求める。エネルギッシュでポジティブ、今すぐ外へ飛び出したくなるような体育会系な口調。", "info": "恐れ知らずでエネルギッシュ。常に新しい刺激を求めて行動します。"},
    "ESFP (エンターテイナー)": {"icon": "💃", "desc": "今を楽しもうとする楽天家。ノリが良く、パーティーのような賑やかで、周囲を明るくする派手な口調。", "info": "好奇心旺盛で、その場を明るく盛り上げる才能に溢れています。"}
}

# 5. メイン画面
st.title("✨ 16タイプ性格変換メーカー")

st.markdown("""
入力した文章を、MBTIの16タイプになりきってリライトします。
自分のタイプならどう言うか、あの人ならどう表現するか、心の個性を楽しんでみてください。
""")

st.subheader("1. タイプを選択")
options = [f"{v['icon']} {k}" for k, v in mbti_data.items()]
selected_option = st.selectbox("どれに変身する？", options)
selected_type = selected_option.split(" ", 1)[1]

# 特徴を表示
st.info(f"**【{selected_type}の特徴】**\n{mbti_data[selected_type]['info']}")

st.subheader("2. 文章を入力")
user_input = st.text_area("何を書き換える？", "今日はいい天気ですね。")

if st.button("変換する！", use_container_width=True):
    with st.spinner("思考回路を書き換え中..."):
        instruction = mbti_data[selected_type]["desc"]
        prompt = f"以下の文章を、{instruction}\n\n文章：{user_input}"
        
        response = model.generate_content(prompt)
        
        st.markdown("### 🎁 変換結果")
        st.success(response.text)
        
        # SNSボタン
        tweet_text = f"【{selected_type}メーカー】で変換したよ！\n\n{response.text[:80]}..."
        tweet_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(tweet_text)}"
        st.markdown(f'<center><a href="{tweet_url}" target="_blank" style="background-color:#1DA1F2;color:white;padding:10px 20px;border-radius:20px;text-decoration:none;">𝕏 でシェアする</a></center>', unsafe_allow_html=True)


# 8. フッター（最下部）
st.markdown("---")
# あなたの𝕏ユーザーID（@以降の英数字）を 'your_screen_name' に入れてください
x_id = "cotty_personal" 
footer_html = f"""
    <div style="text-align: center; color: #888; font-size: 0.8rem;">
        Created by 
        <a href="https://x.com/{x_id}" target="_blank" style="color: #4B9CD3; text-decoration: none;">
            @{x_id}
        </a> 2026
    </div>
"""
st.markdown(footer_html, unsafe_allow_html=True)