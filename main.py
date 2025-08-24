import gradio as gr
from helpers import (
    log, list_audio_files, list_voice_files, delete_file, save_uploaded_voice, save_voice_to_voice_dir
)
from music_workflow import (
    generate_music_workflow, generate_song_with_voice, generate_tts_voice
)

with gr.Blocks(theme=gr.themes.Monochrome(), css=".square-textbox textarea { aspect-ratio: 1/1 !important; min-height:120px; }") as demo:
    gr.Markdown("""
<h1 style='font-family:sans-serif; letter-spacing:2px; color:#222; text-align:center;'>
  <span style="color:#f15a24;">L</span><span style="color:#ff6600;">e</span><span style="color:#ffb347;">o</span><span style="color:#ffcc00;">n</span>
  <span style="color:#f15a24;"> </span>
  <span style="color:#ff6600;">V</span><span style="color:#ffb347;">i</span><span style="color:#ffcc00;">b</span><span style="color:#f15a24;">e</span>
  <span style="color:#222;"> Creator </span>
  <span style="color:#f15a24;">b</span><span style="color:#ff6600;">y</span>
  <span style="color:#ffcc00;"> S</span><span style="color:#ffb347;">u</span><span style="color:#ff6600;">n</span><span style="color:#f15a24;">o</span>
  <span style="color:#ffcc00;">-</span>
  <span style="color:#f15a24;">s</span><span style="color:#ff6600;">т</span><span style="color:#ffb347;">y</span><span style="color:#ffcc00;">l</span><span style="color:#f15a24;">e</span>
</h1>
""")
    with gr.Tab("Create / Enhance Track"):
        gr.Markdown("### Step 1: Create new track")
        with gr.Row():
            prompt_input = gr.Textbox(label="Prompt (e.g.: happy jazz, lofi, etc.)", lines=2, elem_classes="square-textbox", value="lofi relaxing piano")
            with gr.Column():
                track_name_input = gr.Textbox(label="Track name", value="Leon_music", elem_classes="square-textbox")
                duration_input = gr.Slider(minimum=5, maximum=60, value=20, step=1, label="Duration (sec)")
        process_checkbox = gr.Checkbox(label="Enhance audio (ffmpeg)", value=True)
        generate_button = gr.Button("Generate", variant="primary")
        generated_audio_output = gr.Audio(label="Result", type="filepath")

        gr.Markdown("--- \n### Enhance existing track")
        files_list_process = gr.Dropdown(label="Select file", choices=list_audio_files(), interactive=True)
        process_button = gr.Button("Enhance selected")
        processed_audio_output = gr.Audio(label="Enhanced result", type="filepath")
        status_text = gr.Textbox(label="Status", interactive=False)

    with gr.Tab("File Manager"):
        files_list_manage = gr.Dropdown(label="Files list", choices=list_audio_files(), interactive=True)
        with gr.Row():
            play_button = gr.Button("Play")
            delete_button = gr.Button("Delete")
        audio_player = gr.Audio(label="Player", type="filepath")

    with gr.Tab("Sing like Leon!"):
        gr.Markdown("#### 1. Запиши голос, загрузи файл или выбери из сохранённых:")

        with gr.Row():
            record_voice = gr.Audio(
                label="🟢 Записать голос (микрофон)",
                type="filepath",
                source="microphone",
                interactive=True
            )
            upload_voice = gr.Audio(
                label="🟠 Загрузить голос (.wav, без музыки)",
                type="filepath",
                source="upload",
                interactive=True
            )

        voice_files_dropdown = gr.Dropdown(
            label="🟣 Или выбрать из сохранённых",
            choices=list_voice_files(),
            interactive=True
        )
        select_voice_btn = gr.Button("Выбрать/Сохранить голос")
        selected_voice_path = gr.Textbox(label="Путь к выбранному голосу", visible=False)

        # --- Исправленная функция выбора и сохранения ---
        def pick_and_save_voice(upload, record, dropdown):
            # приоритет: upload > record > dropdown
            path = None
            if upload:
                path = save_voice_to_voice_dir(upload)
            elif record:
                path = save_voice_to_voice_dir(record)
            elif dropdown:
                path = dropdown
            # обновить список файлов после сохранения
            files = list_voice_files()
            # если только что выбран/сохранён новый файл — ставим его выбранным
            if path and path in files:
                return path, gr.update(choices=files, value=path)
            else:
                return path, gr.update(choices=files)

        select_voice_btn.click(
            pick_and_save_voice,
            inputs=[upload_voice, record_voice, voice_files_dropdown],
            outputs=[selected_voice_path, voice_files_dropdown]
        )

        gr.Markdown("#### 2. Введи текст и сгенерируй голос (без музыки):")
        lyrics_input = gr.Textbox(
            label="Lyrics/text for TTS",
            lines=4,
            elem_classes="square-textbox"
        )
        generate_tts_btn = gr.Button("Generate TTS Voice")
        tts_result_audio = gr.Audio(label="Synthesized voice", type="filepath")

        generate_tts_btn.click(
            generate_tts_voice,
            inputs=[lyrics_input, selected_voice_path],
            outputs=tts_result_audio,
            show_progress=True
        )

    with gr.Tab("Sing + Instrumental"):
        gr.Markdown("#### 1. Выбери голос, введи текст, жанр и длительность — получи песню:")
        voice_files_dropdown2 = gr.Dropdown(label="Select voice", choices=list_voice_files(), interactive=True)
        lyrics_song_input = gr.Textbox(label="Lyrics", lines=4, elem_classes="square-textbox")
        genre_input = gr.Dropdown(["pop", "rock", "rap", "jazz", "lofi", "electronic"], label="Genre", value="pop")
        duration_input2 = gr.Slider(minimum=10, maximum=60, value=30, step=1, label="Duration (sec)")
        generate_song_btn = gr.Button("Generate Song")
        song_output = gr.Audio(label="Your song", type="filepath")

        generate_song_btn.click(
            generate_song_with_voice,
            inputs=[lyrics_song_input, genre_input, duration_input2, voice_files_dropdown2],
            outputs=song_output,
            show_progress=True
        )

    def on_generate_and_update(prompt, duration, track_name, process_audio):
        result = generate_music_workflow(prompt, duration, track_name, process_audio)
        files = list_audio_files()
        return result, gr.update(choices=files), gr.update(choices=files)

    def on_process_and_update(filepath):
        from ffmpeg_utils import process_existing_audio
        path, status = process_existing_audio(filepath)
        files = list_audio_files()
        return path, status, gr.update(choices=files), gr.update(choices=files)

    generate_button.click(
        on_generate_and_update,
        inputs=[prompt_input, duration_input, track_name_input, process_checkbox],
        outputs=[generated_audio_output, files_list_process, files_list_manage],
        show_progress=True
    )
    process_button.click(
        on_process_and_update,
        inputs=[files_list_process],
        outputs=[processed_audio_output, status_text, files_list_process, files_list_manage],
        show_progress=True
    )
    play_button.click(lambda p: p, inputs=[files_list_manage], outputs=[audio_player])
    delete_button.click(delete_file, inputs=[files_list_manage], outputs=[files_list_process, files_list_manage])

if __name__ == "__main__":
    log("===> Interface loaded! Open in browser: http://127.0.0.1:7860")
    demo.queue()
    demo.launch()