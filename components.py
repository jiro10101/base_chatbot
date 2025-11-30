"""
このファイルは、画面表示に特化した関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import logging
import streamlit as st
import constants as ct


############################################################
# 関数定義
############################################################

def display_app_title():
    """
    タイトル表示
    """
    st.markdown(f"## {ct.APP_NAME}")



def display_initial_ai_message():
    """
    AIメッセージの初期表示
    """
    with st.chat_message("assistant", avatar=ct.AI_ICON_FILE_PATH):
        st.success("わかる条件だけ伝えてくれれば、AIがスクリプトの候補を作ります。")
    # 使用例の表示
    with st.expander("💡 使用例", expanded=False):
        st.markdown("""
        各試験を実施するために必要条件を指定、スクリプトを作成します。
        1.  **FWVer** [試験対象のFWVer]: 例 `1.00`, `1.20`, `1.04`
        2.  **Model** [試験対象の機種]: 例 `ModelA`, `ModelB`, `ModelC`
        3.  **Testscript** [試験スクリプト名]: 例 `/home/jiro/fioスクリプト/rand_read_simple.sh`, `/home/jiro/fioスクリプト/rand_write_simple.sh`, `/home/jiro/fioスクリプト/seq_read_simple.sh`, `/home/jiro/fioスクリプト/seq_write_simple.sh`
        4.  **TestingEnvironment** [試験環境]: 例 `100.67.161.104`, `192.168.20.20`

        **実行例1：全条件を指定**
        ```
        ユーザー: FWVer: 1.00, Testscript: /home/jiro/fioスクリプト/rand_read_simple.sh, Model: ModelA, TestingEnvironment: 100.67.161.104
        AI: /home/jiro/fioスクリプト/Testtoolsqript.sh 1.00 /home/jiro/fioスクリプト/rand_read_simple.sh ModelA 100.67.161.104
        ```

        **実行例2：一部の条件のみ指定**
        ```
        ユーザー: Model: ModelB で FWVer: 1.20
        AI: 以下を指定してください。
            - Testscript [試験スクリプト名]
            - TestingEnvironment [試験環境]
        ```
        """)

def display_conversation_log(chat_message):
    """
    会話ログの一覧表示
    """
    import utils
    
    # 会話ログの最後を表示する時のみ、フィードバック後のメッセージ表示するために「何番目のメッセージか」を取得
    for index, message in enumerate(st.session_state.messages):
        if message["role"] == "assistant":
            with st.chat_message(message["role"], avatar=ct.AI_ICON_FILE_PATH):
                st.markdown(message["content"])
                
                # メッセージが有効なコマンドを含む場合、実行オプションを表示
                # ユーザーメッセージから対応するコマンドを取得
                if index > 0 and index % 2 == 1:  # assistantメッセージのインデックスは奇数
                    user_message_index = index - 1
                    if user_message_index < len(st.session_state.messages):
                        user_message = st.session_state.messages[user_message_index]["content"]
                        validation_result = utils.validate_command_format(user_message)
                        if validation_result["valid"]:
                            display_external_app_launch_option(validation_result["command"])
        else:
            with st.chat_message(message["role"], avatar=ct.USER_ICON_FILE_PATH):
                st.markdown(message["content"])




def display_llm_response(result):
    """
    LLMからの回答表示

    Args:
        result: LLMからの回答
    """
    st.markdown(result)


def display_external_app_launch_option(script_name):
    """
    外部アプリ起動の確認とScreen実行ボタンを表示
    
    Args:
        script_name: 生成されたスクリプト名
    """
    import utils
    
    # サイドバーにScreen実行セクションを表示
    with st.sidebar:
        st.markdown("---")
        st.markdown("## 📺 Screen実行")
        st.info("🚀 スクリプト実行と監視")
        st.markdown("---")
        st.markdown("## 📺 Screen実行")
        st.info("🚀 スクリプト実行と監視")
        
        # 実行結果を保持するためのsession_state初期化
        # 既に値がある場合は初期化しない（上書きしない）
        result_key = f"exec_result_{hash(script_name)}"
        
        import logging
        logger = logging.getLogger(ct.LOGGER_NAME)
        logger.info(f"===== display_external_app_launch_option 呼び出し =====")
        logger.info(f"script_name: {script_name}")
        logger.info(f"result_key: {result_key}")
        logger.info(f"現在のsession_state[result_key]: {st.session_state.get(result_key, '未設定')}")
        
        if result_key not in st.session_state:
            st.session_state[result_key] = None
            logger.info(f"result_keyを初期化: None")
        
        # コマンド表示
        st.markdown("**実行コマンド:**")
        st.code(script_name, language="bash")
        
        # Screen実行ボタン
        if st.button("▶️ Screen実行", key=f"screen_exec_{hash(script_name)}", type="primary", use_container_width=True):
            import logging
            logger = logging.getLogger(ct.LOGGER_NAME)
            logger.info(f"========== ボタンクリック検知 ==========")
            logger.info(f"script_name: {script_name}")
            logger.info(f"result_key: {result_key}")
            
            with st.spinner("Screen実行中..."):
                result = utils.execute_script_with_screen(script_name)
                # 結果をsession_stateに保存
                st.session_state[result_key] = result
                logger.info(f"実行結果をsession_stateに保存: {result}")
                logger.info(f"========== ボタンクリック処理完了 ==========")
                # 画面を再レンダリングして結果を表示
                st.rerun()
        
        # 実行結果の表示
        import logging
        logger = logging.getLogger(ct.LOGGER_NAME)
        logger.info(f"========== 実行結果表示セクション ==========")
        logger.info(f"実行結果表示チェック - result_key: {result_key}, value: {st.session_state.get(result_key, 'None')}")
        
        if st.session_state[result_key] is not None:
            logger.info(f"📌 result is not None: 表示セクションに入りました")
            result = st.session_state[result_key]
            logger.info(f"📌 result内容: {result}")
            logger.info(f"📌 result['success']: {result.get('success', 'キーなし')}")
            
            st.markdown("---")
            st.markdown("### 📊 実行結果")
            
            if result["success"]:
                logger.info(f"✅ st.success()を呼び出します: {result['message']}")
                st.success(f"✅ {result['message']}")
                logger.info(f"✅ st.code()を呼び出します: {result['screen_name']}")
                st.code(f"セッション名: {result['screen_name']}", language="bash")
                
                # セッション接続用のコマンドヒントを表示
                st.info("💡 **セッションへの接続方法**")
                st.code(f"screen -r {result['screen_name']}", language="bash")
                st.caption("※ セッションから離脱するには `Ctrl+A` → `D` を押してください")
            else:
                logger.info(f"❌ st.error()を呼び出します: {result['message']}")
                st.error(f"❌ {result['message']}")
        else:
            logger.info(f"⚠️ result is None: 表示をスキップします")
        
        logger.info(f"========== 実行結果表示セクション終了 ==========")
        
        # Screen セッション一覧
        st.markdown("---")
        st.markdown("### 📋 Screenセッション一覧")
        
        if st.button("🔄 更新", key=f"refresh_sessions_{hash(script_name)}", use_container_width=True):
            st.rerun()
        
        sessions_result = utils.get_screen_sessions()
        if sessions_result["success"]:
            if sessions_result["sessions"]:
                st.caption(f"合計 {len(sessions_result['sessions'])} セッション")
                for session in sessions_result["sessions"]:
                    st.code(session, language="bash")
                
                st.markdown("---")
                st.info("💡 **確認コマンド**")
                st.code("screen -ls", language="bash")
            else:
                st.info("現在アクティブなセッションはありません")
        else:
            st.error(sessions_result["message"])
        
        # テスト結果表示セクション
        st.markdown("---")
        st.markdown("### 📊 最新のテスト結果")
        
        if st.button("🔄 結果更新", key=f"refresh_results_{hash(script_name)}", use_container_width=True):
            st.rerun()
        
        test_results = utils.get_latest_test_results(limit=5)
        
        if test_results["success"] and test_results["results"]:
            st.caption(f"最新 {len(test_results['results'])} 件の結果")
            
            for idx, result in enumerate(test_results["results"], 1):
                with st.expander(f"🔹 {result['timestamp']} - {result['test_type']}", expanded=(idx==1)):
                    st.markdown(f"**FW Ver:** {result['fw_ver']}")
                    st.markdown(f"**Model:** {result['model']}")
                    st.markdown(f"**環境:** {result['environment']}")
                    st.markdown(f"**I/O Type:** {result.get('rw_type', '不明')}")
                    st.markdown(f"**Block Size:** {result.get('bs', '不明')}")
                    st.markdown(f"**I/O Depth:** {result.get('iodepth', '不明')}")
                    
                    # 性能データ
                    if 'read_iops' in result:
                        st.markdown("---")
                        st.markdown("**📈 Read性能**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("IOPS", f"{result['read_iops']:,.0f}")
                        with col2:
                            st.metric("帯域幅", f"{result['read_bw_mb']:.2f} MB/s")
                    
                    if 'write_iops' in result:
                        st.markdown("**📉 Write性能**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("IOPS", f"{result['write_iops']:,.0f}")
                        with col2:
                            st.metric("帯域幅", f"{result['write_bw_mb']:.2f} MB/s")
                    
                    st.caption(f"📄 {result['filename']}")
        else:
            if test_results["success"]:
                st.info("結果ファイルがまだありません")
            else:
                st.warning(test_results["message"])


