import gradio as gr
from helpers import (
    log, list_audio_files, list_voice_files, delete_file, save_voice_to_voice_dir, get_filename_only
)

# Показываем статус загрузки моделей
log("🚀 Starting Leon Vibe Creator...")
log("📦 Loading AI models... (this may take 10-15 seconds)")

from music_workflow import (
    generate_music_workflow, generate_song_with_voice, generate_tts_voice
)

log("🎉 All models loaded! Ready to create music!")

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
    
    with gr.Tab("Create Track"):
        gr.Markdown("### 🎵 Create new music track")
        with gr.Row():
            prompt_input = gr.Textbox(label="Prompt (e.g.: happy jazz, lofi, etc.)", lines=2, elem_classes="square-textbox", value="lofi relaxing piano")
            with gr.Column():
                track_name_input = gr.Textbox(label="Track name", value="Leon_music", elem_classes="square-textbox")
                duration_input = gr.Slider(minimum=5, maximum=60, value=20, step=1, label="Duration (sec)")
        
        generate_button = gr.Button("🎵 Generate Track", variant="primary", size="lg")
        
        status_generate = gr.Textbox(label="Status", value="Ready to generate", interactive=False)
        generated_audio_output = gr.Audio(label="Generated Track", type="filepath")

    with gr.Tab("File Manager"):
        gr.Markdown("### 📂 Manage your files")
        
        # Отображаем только названия файлов, а не полные пути
        def get_audio_files_display():
            files = list_audio_files()
            return [(get_filename_only(f), f) for f in files]
        
        files_list_manage = gr.Dropdown(
            label="📁 Audio Files", 
            choices=get_audio_files_display(), 
            interactive=True
        )
        
        with gr.Row():
            play_button = gr.Button("▶️ Play", variant="secondary")
            delete_button = gr.Button("🗑️ Delete", variant="stop")
        audio_player = gr.Audio(label="🎵 Player", type="filepath")

    with gr.Tab("Record Voice"):
        gr.Markdown("### 🎤 Записать ваш голос")
        gr.Markdown("*Запишите чистый голос без музыки. Рекомендуется 10-30 секунд.*")
        
        with gr.Tabs():
            with gr.Tab("🔴 Записать с микрофона"):
                record_voice = gr.Audio(
                    label="Нажмите кнопку записи и говорите",
                    type="filepath",
                    source="microphone"
                )
                
            with gr.Tab("📁 Загрузить файл"):
                upload_voice = gr.Audio(
                    label="Выберите .wav файл с вашим голосом",
                    type="filepath",
                    source="upload"
                )
        
        # Предварительный просмотр и управление
        with gr.Row():
            with gr.Column(scale=2):
                voice_preview = gr.Audio(
                    label="🎧 Предварительный просмотр", 
                    type="filepath",
                    visible=False
                )
                
            with gr.Column(scale=1):
                voice_info = gr.Textbox(
                    label="ℹ️ Статус", 
                    value="Запишите или загрузите голос",
                    interactive=False
                )
        
        with gr.Row():
            voice_name_input = gr.Textbox(
                label="📝 Название голоса (например: 'Мой голос', 'Leon voice')",
                placeholder="Введите название для сохранения",
                visible=False
            )
            
        with gr.Row():
            save_voice_btn = gr.Button(
                "💾 Сохранить в библиотеку голосов", 
                variant="primary",
                size="lg",
                visible=False
            )
            
        # Скрытые поля
        current_voice_path = gr.Textbox(visible=False)
        
        # Библиотека голосов на этой же странице
        gr.Markdown("---")
        gr.Markdown("### 📚 Ваши сохраненные голоса")
        
        def get_voice_files_display():
            files = list_voice_files()
            return [(get_filename_only(f), f) for f in files]
        
        saved_voices_list = gr.Dropdown(
            label="🎤 Сохраненные голоса",
            choices=get_voice_files_display(),
            interactive=True
        )
        
        with gr.Row():
            refresh_voices_btn = gr.Button("🔄 Обновить список", variant="secondary")
            play_saved_voice_btn = gr.Button("▶️ Прослушать", variant="secondary")
            delete_voice_btn = gr.Button("🗑️ Удалить голос", variant="stop")
            
        saved_voice_player = gr.Audio(label="🔊 Воспроизведение голоса", type="filepath")

    with gr.Tab("Voice Synthesis"):
        gr.Markdown("### 🗣️ Синтез голоса")
        
        voice_selector = gr.Dropdown(
            label="🎤 Выберите голос для синтеза",
            choices=get_voice_files_display(),
            interactive=True
        )
        
        lyrics_input = gr.Textbox(
            label="📝 Текст для синтеза",
            lines=6,
            placeholder="Введите текст...\n\nShift+Enter для новой строки",
            max_lines=10
        )
        
        generate_tts_btn = gr.Button("🎤 Синтезировать", variant="primary", size="lg")
        
        status_tts = gr.Textbox(label="🎙️ Статус", value="Выберите голос и введите текст", interactive=False)
        tts_result_audio = gr.Audio(label="🔊 Результат", type="filepath")

    with gr.Tab("Complete Song"):
        gr.Markdown("### 🎵 Создать песню с голосом")
        
        voice_selector_song = gr.Dropdown(
            label="🎤 Голос для песни",
            choices=get_voice_files_display(),
            interactive=True
        )
        
        lyrics_song_input = gr.Textbox(
            label="📝 Текст песни", 
            lines=8, 
            placeholder="Введите слова песни...\n\nShift+Enter для новой строки",
            max_lines=15
        )
        
        with gr.Row():
            genre_input = gr.Dropdown(
                ["pop", "rock", "rap", "jazz", "lofi", "electronic"], 
                label="🎸 Жанр", 
                value="pop"
            )
            duration_input2 = gr.Slider(
                minimum=10, 
                maximum=60, 
                value=30, 
                step=1, 
                label="⏱️ Длительность (сек)"
            )
        
        generate_song_btn = gr.Button("🎬 Создать песню", variant="primary", size="lg")
        
        status_song = gr.Textbox(label="🎼 Статус", value="Выберите голос и введите текст", interactive=False)
        song_output = gr.Audio(label="🎊 Готовая песня", type="filepath")

    # === ФУНКЦИИ ОБРАБОТКИ ===
    
    # Обработка записи/загрузки голоса
    def handle_voice_input(record_file, upload_file):
        """Обрабатывает запись или загрузку голоса"""
        current_file = upload_file if upload_file else record_file
        
        if current_file:
            return (
                current_file,  # voice_preview
                gr.update(visible=True),  # voice_preview visibility
                gr.update(visible=True, value="leon_voice"),  # voice_name_input
                gr.update(visible=True),  # save_voice_btn
                "✅ Голос загружен! Введите название и сохраните",  # voice_info
                current_file  # current_voice_path
            )
        else:
            return (
                None,  # voice_preview
                gr.update(visible=False),  # voice_preview visibility  
                gr.update(visible=False),  # voice_name_input
                gr.update(visible=False),  # save_voice_btn
                "Запишите или загрузите голос",  # voice_info
                None  # current_voice_path
            )
    
    # Сохранение голоса с пользовательским названием
    def save_voice_with_name(voice_path, voice_name):
        """Сохраняет голос с пользовательским названием"""
        if not voice_path:
            return "❌ Нет голоса для сохранения", gr.update(), gr.update()
        
        if not voice_name or not voice_name.strip():
            return "❌ Введите название голоса", gr.update(), gr.update()
        
        try:
            saved_path = save_voice_to_voice_dir(voice_path, voice_name.strip())
            new_choices = get_voice_files_display()
            
            return (
                "✅ Голос сохранен успешно!",
                gr.update(choices=new_choices),
                gr.update(choices=new_choices)
            )
        except Exception as e:
            return f"❌ Ошибка сохранения: {str(e)}", gr.update(), gr.update()
    
    # Функции для основного функционала
    def on_generate_and_update(prompt, duration, track_name, progress=gr.Progress()):
        try:
            def update_status(percent, desc):
                progress(percent, desc=desc)
                return desc
                
            result = generate_music_workflow(prompt, duration, track_name, update_status)
            
            # Обновляем список файлов
            new_choices = get_audio_files_display()
            
            return result, gr.update(choices=new_choices), "✅ Трек создан!"
        except Exception as e:
            return None, gr.update(), f"❌ Ошибка: {str(e)}"

    def on_generate_tts(lyrics, voice_path, progress=gr.Progress()):
        try:
            if not lyrics.strip():
                return None, "❌ Введите текст"
            if not voice_path:
                return None, "❌ Выберите голос"
                
            def update_status(percent, desc):
                progress(percent, desc=desc)
                return desc
                
            result = generate_tts_voice(lyrics, voice_path, update_status)
            return result, "✅ Голос синтезирован!"
        except Exception as e:
            return None, f"❌ Ошибка: {str(e)}"

    def on_generate_song(lyrics, genre, duration, voice_path, progress=gr.Progress()):
        try:
            if not lyrics.strip():
                return None, "❌ Введите текст песни"
            if not voice_path:
                return None, "❌ Выберите голос"
                
            def update_status(percent, desc):
                progress(percent, desc=desc)
                return desc
                
            result = generate_song_with_voice(lyrics, genre, duration, voice_path, update_status)
            return result, "✅ Песня создана!"
        except Exception as e:
            return None, f"❌ Ошибка: {str(e)}"

    # Функции для управления файлами
    def refresh_voice_lists():
        """Обновляет все списки голосов"""
        new_choices = get_voice_files_display()
        return (
            gr.update(choices=new_choices),  # saved_voices_list
            gr.update(choices=new_choices),  # voice_selector
            gr.update(choices=new_choices)   # voice_selector_song
        )
    
    def refresh_audio_files():
        """Обновляет список аудио файлов"""
        new_choices = get_audio_files_display()
        return gr.update(choices=new_choices)

    def on_delete_audio_file(filepath):
        """Удаляет аудио файл"""
        if filepath:
            delete_file(filepath)
        return refresh_audio_files()

    def on_delete_voice_file(filepath):
        """Удаляет файл голоса"""
        if filepath:
            delete_file(filepath)
        return refresh_voice_lists()

    # === ПОДКЛЮЧЕНИЕ СОБЫТИЙ ===
    
    # Обработка голоса
    record_voice.change(
        handle_voice_input,
        inputs=[record_voice, upload_voice],
        outputs=[voice_preview, voice_preview, voice_name_input, save_voice_btn, voice_info, current_voice_path]
    )
    
    upload_voice.change(
        handle_voice_input,
        inputs=[record_voice, upload_voice],
        outputs=[voice_preview, voice_preview, voice_name_input, save_voice_btn, voice_info, current_voice_path]
    )
    
    save_voice_btn.click(
        save_voice_with_name,
        inputs=[current_voice_path, voice_name_input],
        outputs=[voice_info, saved_voices_list, voice_selector]
    )
    
    # Управление голосами
    refresh_voices_btn.click(
        refresh_voice_lists,
        outputs=[saved_voices_list, voice_selector, voice_selector_song]
    )
    
    play_saved_voice_btn.click(
        lambda x: x,
        inputs=[saved_voices_list],
        outputs=[saved_voice_player]
    )
    
    delete_voice_btn.click(
        on_delete_voice_file,
        inputs=[saved_voices_list],
        outputs=[saved_voices_list, voice_selector, voice_selector_song]
    )
    
    # Основной функционал
    generate_button.click(
        on_generate_and_update,
        inputs=[prompt_input, duration_input, track_name_input],
        outputs=[generated_audio_output, files_list_manage, status_generate]
    )
    
    generate_tts_btn.click(
        on_generate_tts,
        inputs=[lyrics_input, voice_selector],
        outputs=[tts_result_audio, status_tts]
    )
    
    generate_song_btn.click(
        on_generate_song,
        inputs=[lyrics_song_input, genre_input, duration_input2, voice_selector_song],
        outputs=[song_output, status_song]
    )
    
    # Управление файлами
    play_button.click(
        lambda p: p, 
        inputs=[files_list_manage], 
        outputs=[audio_player]
    )
    
    delete_button.click(
        on_delete_audio_file,
        inputs=[files_list_manage],
        outputs=[files_list_manage]
    )

if __name__ == "__main__":
    log("===> Interface loaded! Open in browser: http://127.0.0.1:7860")
    demo.queue()
    demo.launch()