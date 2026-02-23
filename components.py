"""
Streamlit の UI コンポーネント（タイトル・会話ログ・サイドバー）を描画するファイル。
ロジックは持たず、表示処理のみを担当する。
"""

import logging
import streamlit as st
import constants as ct


def display_app_title():
    """アプリタイトルを表示する"""
    st.markdown(f"## {ct.APP_NAME}")


def display_initial_ai_message():
    """
    初回表示時のAIウェルカムメッセージと使用例を表示する。
    使用例は expander で折りたたんで表示する。
    """
    d = ct.FIO_SCRIPT_DIR
    with st.chat_message("assistant", avatar=ct.AI_ICON_FILE_PATH):
        st.success("わかる条件だけ伝えてくれれば、AIがスクリプトの候補を作ります。")
    # 使用例の表示
    with st.expander("💡 使用例", expanded=False):
        st.markdown(f"""
        各試験を実施するために必要条件を指定、スクリプトを作成します。
        1.  **FWVer** [試験対象のFWVer]: 例 `1.00`, `1.20`, `1.04`
        2.  **Model** [試験対象の機種]: 例 `ModelA`, `ModelB`, `ModelC`
        3.  **Testscript** [試験スクリプト名]: 例 `{d}/rand_read_simple.sh`, `{d}/rand_write_simple.sh`, `{d}/seq_read_simple.sh`, `{d}/seq_write_simple.sh`
        4.  **TestingEnvironment** [試験環境]: 例 `100.67.161.104`, `192.168.20.20`

        **実行例1：全条件を指定**
        ```
        ユーザー: FWVer: 1.00, Testscript: {d}/rand_read_simple.sh, Model: ModelA, TestingEnvironment: 100.67.161.104
        AI: {d}/Testtoolsqript.sh 1.00 {d}/rand_read_simple.sh ModelA 100.67.161.104
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
    session_state.messages をもとに会話ログを再描画する。
    Streamlit の再実行モデルにより、送信のたびにこの関数が呼ばれる。
    """
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            with st.chat_message(message["role"], avatar=ct.AI_ICON_FILE_PATH):
                st.markdown(message["content"])
        else:
            with st.chat_message(message["role"], avatar=ct.USER_ICON_FILE_PATH):
                st.markdown(message["content"])




def display_llm_response(result):
    """LLMの応答テキストをマークダウンで表示する"""
    st.markdown(result)


def display_sidebar():
    """
    サイドバーを2タブ構成で表示する。
      Tab1（Screen実行）: 現在のコマンド確認・実行・セッション一覧
      Tab2（テスト結果）: 最新の fio 結果ファイルを読み込んで表示

    utils を関数内でインポートしているのは、
    components ↔ utils の循環インポートを避けるため。
    """
    import utils

    with st.sidebar:
        tab1, tab2 = st.tabs(["▶ Screen実行", "📊 テスト結果"])

        # ==========================================
        # Tab1: Screen実行
        # ==========================================
        with tab1:
            if st.session_state.current_command:
                st.markdown("**実行コマンド:**")
                st.code(st.session_state.current_command, language="bash")

                # exec_result が未実行（None）か失敗の場合のみボタンを表示
                exec_not_done = st.session_state.exec_result is None
                exec_failed = (
                    st.session_state.exec_result is not None
                    and not st.session_state.exec_result.get("success", False)
                )
                if exec_not_done or exec_failed:
                    if st.button("▶️ Screen実行", key="screen_exec_btn", type="primary", use_container_width=True):
                        with st.spinner("Screen実行中..."):
                            exec_result = utils.execute_script_with_screen(st.session_state.current_command)
                            st.session_state.exec_result = exec_result
                        st.rerun()

                # 実行結果の表示
                if st.session_state.exec_result is not None:
                    st.markdown("---")
                    st.markdown("### 📊 実行結果")
                    if st.session_state.exec_result["success"]:
                        st.success(f"✅ {st.session_state.exec_result['message']}")
                        st.code(f"セッション名: {st.session_state.exec_result['screen_name']}", language="bash")
                        st.info("💡 **セッションへの接続方法**")
                        st.code(f"screen -r {st.session_state.exec_result['screen_name']}", language="bash")
                        st.caption("※ セッションから離脱するには `Ctrl+A` → `D` を押してください")
                    else:
                        st.error(f"❌ {st.session_state.exec_result['message']}")
            else:
                st.info("💬 チャットでパラメータを指定すると、ここに実行コマンドが表示されます。")

            # Screenセッション一覧
            st.markdown("---")
            st.markdown("### 📋 Screenセッション一覧")
            if st.button("🔄 更新", key="refresh_sessions_btn", use_container_width=True):
                st.rerun()

            sessions_result = utils.get_screen_sessions()
            if sessions_result["success"]:
                if sessions_result["sessions"]:
                    st.caption(f"合計 {len(sessions_result['sessions'])} セッション")
                    for session in sessions_result["sessions"]:
                        st.code(session, language="bash")
                    st.info("💡 **確認コマンド**")
                    st.code("screen -ls", language="bash")
                else:
                    st.info("現在アクティブなセッションはありません")
            else:
                st.error(sessions_result["message"])

        # ==========================================
        # Tab2: テスト結果
        # ==========================================
        with tab2:
            if st.button("🔄 結果更新", key="refresh_results_btn", use_container_width=True):
                st.rerun()

            test_results = utils.get_latest_test_results(limit=5)

            if test_results["success"] and test_results["results"]:
                st.caption(f"最新 {len(test_results['results'])} 件の結果")
                for idx, result in enumerate(test_results["results"], 1):
                    with st.expander(f"🔹 {result['timestamp']} - {result['test_type']}", expanded=(idx == 1)):
                        st.markdown(f"**FW Ver:** {result['fw_ver']}")
                        st.markdown(f"**Model:** {result['model']}")
                        st.markdown(f"**環境:** {result['environment']}")
                        st.markdown(f"**I/O Type:** {result.get('rw_type', '不明')}")
                        st.markdown(f"**Block Size:** {result.get('bs', '不明')}")
                        st.markdown(f"**I/O Depth:** {result.get('iodepth', '不明')}")

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


