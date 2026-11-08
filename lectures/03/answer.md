# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
  - 素のLLM（app.ask）は講座を知らないため、「難易度別」「理解度別」などの一般論を推測で並べ、正解を答えられなかった（出力709トークン）。
  - エージェントは用語集を検索し、「基礎・実装・発展の3段階で、どれか1つで完了」と用語集どおりに答え、最後に「第1回」と示した（出力150トークン）。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
  - 「3レベル」の質問：search_glossary({'query': '3レベル'})
  - 「LoRAとQLoRAの違いは？」：search_glossary({'query': 'LoRA'}) と search_glossary({'query': 'QLoRA'}) の2回。docstring の「query には調べたい用語を1つだけ入れる」に従い、用語を1つずつ検索していた。
- 1つの質問での LLM 呼び出し回数（`requests`）：
  - どちらも2回（検索を決める1回と、結果を読んで回答する1回）。LoRA/QLoRAでは2つの検索を1回でまとめて依頼したため、tool_calls=2 でも requests=2 だった。
- 追加したツールと、docstring に書いた説明：
  - 演習の make_quiz の代わりに、宿題で save_learning_log を追加した（宿題欄を参照）。

## 宿題

- 取り組んだレベル：実装
- やったこと：
  - app/tools.py に save_learning_log(title, content) を追加し、learning_log/ に Markdown で保存するようにした。本文が空・長すぎる場合は保存せず、"x" モードで同名ファイルを上書きしないようにした。
  - app/agent.py で requires_approval=True を付けて登録し、output_type に DeferredToolRequests を加えた。
  - CLI では承認待ちの呼び出しごとに title と content を表示して y/N を聞き、DeferredToolResults と message_history を渡して run_sync で続きを実行するようにした。
  - INSTRUCTIONS に「学習の記録や保存を頼まれたら save_learning_log を使う。頼まれていなければ保存しない。」を追加した。
- 結果：
  - --list-tools でツールが3個になり、pytest は17件すべて通った。
  - 最初の docstring（最後の文が「実行の前に利用者の承認を求める」）では、save_learning_log が呼ばれなかった。モデルが回答の文章の中で「保存してよろしいでしょうか？」と自分で聞いて終わった（tool_calls=2 は search_glossary のみ、requests=2）。
  - docstring の最後の文だけを「保存してよいかの確認はプログラムが自動で行うので、確認の質問はせず、そのままこのツールを呼ぶこと」に変えると、モデルは確認の質問をせずに save_learning_log を呼び、ハーネスが [承認待ち] で止めるようになった。
  - (a) y で承認：search_glossary({'query': 'LoRA'})、search_glossary({'query': 'QLoRA'}) の後に save_learning_log({'title': 'LoRAとQLoRAの違い', 'content': '# LoRAとQLoRAの違い…'}) が呼ばれ、[承認待ち] で title と content が表示された。y を入力すると「保存しました: learning_log/20261108-170709_LoRAとQLoRAの違い.md」が返り、承認した content と同じ内容のファイルができた。[usage] は requests=1, tool_calls=1 と表示されたが、これは承認後に再開した run_sync の分だけで、実際には Gemini を3回呼んでいた。
  - (b) n で拒否：search_glossary({'query': 'RAG'}) の後に save_learning_log が呼ばれ、[承認待ち] で N を入力すると、関数は実行されず「利用者が保存を許可しませんでした。」がツールの結果としてモデルに返った。learning_log/ のファイルは増えず、モデルは「保存の許可が得られなかったため保存はキャンセルされました」と回答した。拒否後に保存を再試行することはなかった（requests=1 は再開後の分のみ）。
  - (c) 保存を頼まない質問（「RAGとは？」）：search_glossary({'query': 'RAG'}) だけが呼ばれ、save_learning_log は呼ばれず [承認待ち] も出なかった（requests=2, tool_calls=1。承認による中断がないので全体の回数がそのまま表示された）。今回は「用語集に直接の定義はありませんでした」と正直に伝えてから一般的な説明をしており、(b) と同じ検索結果でも回によって答え方が変わった。
- 気づき・疑問：
  - 承認の仕組みはハーネス側にあるのに、docstring に「承認を求める」と書くと、モデルが自分で確認しようとしてツールを呼ばなくなった。docstring は人間向けの説明ではなく、モデルへの指示として読まれるので、「誰が何をするか」をはっきり書く必要があると分かった。
  - 承認の前に、モデルが作った title と content を人が確認できるので、意図しない保存を防げる。実際に (b) では、content に「大規模言語模型」という誤りがあるのに承認画面で気づけた。止める仕組みをモデルではなくプログラム側に持たせる意味を実感した。
  - 用語集に RAG はないが、「一致率」の別名 inter-rater agreement に "rag" が含まれるため、部分一致でヒットした。モデルは関係のない結果を無視して自分の知識で答え、「用語集に定義は登録されています」と事実と違うことを書いた。ツールが的外れな結果を返すと、INSTRUCTIONS の「見つからなければ推測しない」が守られないことがある。
  - 承認で実行が2回の run_sync に分かれるため、[usage] は再開後の分だけが表示され、実際の LLM 呼び出し回数より少なく見えた。料金や回数の上限を管理するなら、usage を引き継いで合計する必要がある。
  - 疑問：title から見出しを付けているのに、モデルが content の先頭にも同じ見出しを書いたため、ファイルの見出しが重複した。docstring に「content に見出しは不要」と書けば防げるか。また、複数のツールが同時に承認待ちになったとき、1件ずつ聞くのと、まとめて聞くのとでは、どちらが利用者にとって安全か。