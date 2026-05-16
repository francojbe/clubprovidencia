from playwright.sync_api import sync_playwright
import time

def run():
    print("Iniciando modo debug...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("Navegando a login de ClassPass...")
        page.goto("https://studios.classpass.com/login")
        
        print("Ingresando credenciales...")
        try:
            # Handle cookie banner first
            try:
                page.click('button:has-text("De acuerdo")', timeout=2000)
                print("Banner de cookies aceptado.")
            except:
                print("No se encontró banner de cookies, continuando...")

            page.fill('input[name="email"], input[type="email"]', "reservasexternas@clubprovidencia.cl")
            page.fill('input[name="password"], input[type="password"]', "club123")
            
            # Press enter to submit instead of clicking the button (in case it's still covered)
            page.keyboard.press("Enter")
        except Exception as e:
            print(f"No se pudieron ingresar credenciales automáticamente: {e}")
        
        print("Esperando 5 segundos después del click...")
        page.wait_for_timeout(5000)
        
        print("====== MODO DEBUG ======")
        print("Navegador ABIERTO. El script no se cerrará hasta que lo detengas en la terminal o pasen 60 minutos.")
        print("Revisa la ventana del navegador. Dime qué ves o qué debo hacer después.")
        
        # Mantener abierto
        time.sleep(3600)

if __name__ == "__main__":
    run()
