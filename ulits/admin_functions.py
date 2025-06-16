from main import bot


def format_entities(text, entities):
    formatted_text = text
    shift = 0 

    for entity in entities:
        entity_type = entity['type']
        offset = entity['offset']
        length = entity['length'] 

        entity_text = text[offset:offset + length]

        if entity_type == 'bold':
            formatted_text = (
                formatted_text[:offset + shift] +
                f"<b>{entity_text}</b>" +
                formatted_text[offset + length + shift:]
            )
            shift += 7 
        elif entity_type == 'italic':
            formatted_text = (
                formatted_text[:offset + shift] +
                f"<i>{entity_text}</i>" +
                formatted_text[offset + length + shift:]
            )
            shift += 7 
            
        elif entity_type == 'pre':
            formatted_text = (
                formatted_text[:offset + shift] +
                f"<code>{entity_text}</code>" +
                formatted_text[offset + length + shift:]
            )
        elif entity_type == 'code': 
            formatted_text = (
                formatted_text[:offset + shift] +
                f"<code>{entity_text}</code>" +
                formatted_text[offset + length + shift:]
            )
            shift += 13 
        elif entity_type == 'strikethrough':
            formatted_text = (
                formatted_text[:offset + shift] +
                f"<s>{entity_text}</s>" +
                formatted_text[offset + length + shift:]
            )
            shift += 7  
        elif entity_type == 'underline':
            formatted_text = (
                formatted_text[:offset + shift] +
                f"<u>{entity_text}</u>" +
                formatted_text[offset + length + shift:]
            )
            shift += 7 
        elif entity_type == 'blockquote':
            formatted_text = (
                formatted_text[:offset + shift] +
                f"<blockquote>{entity_text}</blockquote>" +
                formatted_text[offset + length + shift:]
            )
            shift += 25 

    return formatted_text


async def download_media(file_id, file_path):
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, file_path)

def parse_url_buttons(text):
    buttons = []
    lines = text.split('\n')
    for line in lines:
        if ' | ' in line:
            parts = line.split(' | ')
            row = []
            for part in parts:
                button_parts = part.split(' - ')
                if len(button_parts) == 2:
                    button_text = button_parts[0].strip()
                    button_url = button_parts[1].strip()
                    row.append((button_text, button_url))
            buttons.append(row)
        else:
            button_parts = line.split(' - ')
            if len(button_parts) == 2:
                button_text = button_parts[0].strip()
                button_url = button_parts[1].strip()
                buttons.append([(button_text, button_url)])
    return buttons

def parse_existing_url_buttons(existing_buttons):
    buttons = []
    for row in existing_buttons:
        button_row = []
        for button in row:
            button_text = button.text
            button_url = button.url
            button_row.append((button_text, button_url))
        buttons.append(button_row)
    return buttons



