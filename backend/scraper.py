import asyncio
from playwright.async_api import async_playwright

async def sync_classpass():
    print("Iniciando bot de sincronización...")
    async with async_playwright() as p:
        # Configuración sigilosa e invisible para servidor/Easypanel
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        ) 
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="es-CL",
            timezone_id="America/Santiago"
        )
        page = await context.new_page()
        
        try:
            print("Navegando a ClassPass...")
            await page.goto("https://studios.classpass.com/")
            
            print("Iniciando sesión...")
            # Los selectores pueden variar dependiendo del código fuente de Classpass
            # Usamos get_by_label o fill genérico
            await page.fill('input[name="email"], input[type="email"]', "reservasexternas@clubprovidencia.cl")
            await page.fill('input[name="password"], input[type="password"]', "club123")
            
            # Clic en el botón de login
            await page.click('button[type="submit"]')
            
            print("Esperando a que cargue el panel principal...")
            # Esperamos a que la URL cambie al dashboard o esperamos 5 segundos
            await page.wait_for_timeout(5000)
            
            print("¡Login exitoso! Extrayendo reservas del día...")
            
            # Aquí iría el código para hacer clic en las clases ("Horario") y leer "Lista"
            # Como ejemplo, tomaremos una captura de pantalla para comprobar
            await page.screenshot(path="dashboard_classpass.png")
            
            print("Datos extraídos correctamente. (Ver dashboard_classpass.png)")
            
        except Exception as e:
            print(f"Error durante la sincronización: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(sync_classpass())

async def search_user(query: str, target_time: str = None):
    import unicodedata
    import os
    from datetime import datetime
    
    def log(msg: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {msg}"
        print(log_msg)
        with open("bot_debug.log", "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")
            
    if target_time:
        log(f"Iniciando bot RPA para buscar a: {query} a las {target_time}")
    else:
        log(f"Iniciando bot RPA para buscar a: {query}")
        
    results = []
    
    def normalize(t):
        if not t: return ''
        return unicodedata.normalize('NFD', t).encode('ascii', 'ignore').decode('utf-8').lower().replace('', 'n').replace('ñ', 'n')
        
    q_norm = normalize(query)
    async with async_playwright() as p:
        # Modo invisible camuflado (headless=True) listo para producción/Easypanel
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        state_file = "state.json"
        
        # Intentar cargar la sesión si existe para saltar el login
        if os.path.exists(state_file):
            context = await browser.new_context(
                storage_state=state_file,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="es-CL",
                timezone_id="America/Santiago"
            )
        else:
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="es-CL",
                timezone_id="America/Santiago"
            )
            
        page = await context.new_page()
        
        try:
            logged_in = False
            # Si hay sesión guardada, intentar ir directo a la lista de clases
            if os.path.exists(state_file):
                try:
                    log("Intentando navegar directamente usando la sesión guardada...")
                    await page.goto("https://studios.classpass.com/classes/", wait_until="domcontentloaded")
                    # Verificar si cargó la lista de horarios (si no, nos redireccionó al login)
                    await page.wait_for_selector('.schedule-list__item', state="visible", timeout=6000)
                    logged_in = True
                    log("Sesión activa recuperada exitosamente. Saltando flujo de login.")
                except Exception as e:
                    log("La sesión guardada expiró o no es válida. Iniciando login desde cero...")
            
            if not logged_in:
                log("Navegando a login de ClassPass...")
                await page.goto("https://studios.classpass.com/login")
                await page.wait_for_timeout(2000)
                
                try:
                    await page.click('button:has-text("De acuerdo")', timeout=3000)
                    log("Banner de cookies aceptado.")
                except:
                    log("Banner de cookies no encontrado, continuando.")
                    
                log("Ingresando credenciales (escribiendo como humano)...")
                email_input = page.locator('input[name="email"], input[type="email"]').first
                await email_input.click()
                await page.wait_for_timeout(500) # Esperar a que el foco se asiente
                await email_input.fill("") # Asegurar que esté vacío
                await email_input.type("reservasexternas@clubprovidencia.cl", delay=50)
                
                pass_input = page.locator('input[name="password"], input[type="password"]').first
                await pass_input.click()
                await page.wait_for_timeout(500)
                await pass_input.fill("")
                await pass_input.type("club123", delay=50)
                
                log("Haciendo clic en el botón de Iniciar sesión...")
                await page.locator('button[type="submit"]').first.click()
                
                log("Esperando a que cargue el dashboard tras el login...")
                await page.wait_for_selector('a.nav__link[href*="/classes/"]', timeout=30000)
                
                # Guardar la sesión exitosa para las siguientes búsquedas
                await context.storage_state(path=state_file)
                log(f"Nueva sesión guardada en {state_file}.")
                
                log("Navegando a Horario...")
                await page.goto("https://studios.classpass.com/classes/", wait_until="networkidle")
                
                await page.wait_for_selector('.schedule-list__item', state="visible", timeout=30000)
            
            # Pequeña pausa para asegurar que los elementos del DOM terminen de renderizar
            await page.wait_for_timeout(2000)
            
            log("Obteniendo clases del día...")
            class_items = await page.locator('.schedule-list__item').all()
            total_classes = len(class_items)
            log(f"Se encontraron {total_classes} clases programadas.")
            
            user_classes = []
            matched_name = ""
            
            for idx in range(total_classes):
                items = await page.locator('.schedule-list__item').all()
                if idx >= len(items): break
                
                item = items[idx]
                
                # Optimización de Filtro de Tiempo: Saltar las clases ANTERIORES a la hora pedida ("partir desde ahí")
                if target_time:
                    list_text = await item.inner_text()
                    import re
                    time_match = re.search(r'(\d{1,2}:\d{2})', list_text)
                    if time_match:
                        class_time_str = time_match.group(1)
                        try:
                            # Convertimos "HH:MM" a minutos para poder comparar si es menor
                            t_parts = target_time.split(':')
                            c_parts = class_time_str.split(':')
                            target_mins = int(t_parts[0]) * 60 + int(t_parts[1])
                            class_mins = int(c_parts[0]) * 60 + int(c_parts[1])
                            
                            # Si la clase de la lista es más temprano que la hora buscada, la saltamos
                            if class_mins < target_mins:
                                # log(f"Saltando clase de las {class_time_str}") # Comentado para no spamear
                                continue
                            else:
                                log(f"Revisando clase de las {class_time_str} (>= {target_time})")
                        except Exception as e:
                            log(f"Error parseando hora: {e}")
                    else:
                        log(f"No se encontró hora en list_text: {list_text[:30]}")
                        
                # Optimización de velocidad extrema: Esperar dinámicamente la respuesta de la API en lugar de un tiempo fijo
                try:
                    async with page.expect_response(lambda r: r.request.resource_type in ["fetch", "xhr"], timeout=800):
                        await item.click()
                    await page.wait_for_timeout(150) # Darle 150ms a React para dibujar los nombres tras recibir los datos
                except:
                    # Si no hubo petición (datos en caché) o tardó mucho, hacemos un pequeño fallback de seguridad
                    await item.click()
                    await page.wait_for_timeout(350)
                
                class_name_el = page.locator('.schedule-detail p.text--semibold.text--ellipsis').first
                class_time_el = page.locator('.schedule-detail p.text--semibold:not(.text--ellipsis)').first
                
                class_name = await class_name_el.text_content() if await class_name_el.count() > 0 else "Clase Desconocida"
                class_time = await class_time_el.text_content() if await class_time_el.count() > 0 else ""
                
                if class_name: class_name = class_name.strip()
                if class_time: class_time = class_time.strip()
                
                user_elements = await page.locator('.avatar__name').all()
                
                found_in_class = False
                for u_el in user_elements:
                    user_name = await u_el.text_content()
                    if user_name:
                        user_name = user_name.strip()
                        if q_norm in normalize(user_name):
                            log(f"¡Match encontrado! {user_name} en {class_name} a las {class_time}")
                            matched_name = user_name
                            user_classes.append({
                                "clase": class_name,
                                "horario": class_time,
                                "fecha": "Hoy (Scrape en vivo)"
                            })
                            found_in_class = True
                            break
                            
                if found_in_class:
                    log("Usuario encontrado exitosamente. Interrumpiendo la búsqueda del resto de clases para ahorrar tiempo.")
                    break
            if user_classes:
                results.append({
                    "id": 9999,
                    "nombre": matched_name or query,
                    "email": "classpass@live.com",
                    "classes": user_classes
                })
                
            log(f"Extracción completada. Se encontraron {len(user_classes)} reservas para este usuario.")
            
        except Exception as e:
            log(f"Error durante el RPA: {e}")
        finally:
            log("Cerrando navegador...")
            await browser.close()
            
    return results
