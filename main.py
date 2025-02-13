import os
import shutil
from datetime import datetime
import subprocess
from together import Together
from dotenv import load_dotenv

load_dotenv()


def read_file(filename: str):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()


def resume_prompt_builder(main_tex, base_prompt_text, job_desc_text):
    master_resume = read_file(main_tex).split("%%%%%%  RESUME STARTS HERE  %%%%%%")[1]
    base_prompt = read_file(base_prompt_text)
    job_desc = read_file(job_desc_text)

    final_prompt = f"""
    {base_prompt}

    <master_resume>
    {master_resume}
    </master_resume>

    <job_desc>
    {job_desc}
    </job_desc>
    """
    return final_prompt


def generate_pdf(latex_content):
    print('generating PDF...')

    tex_file = "resume.tex"
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(latex_content)

    with open(os.devnull, 'w') as devnull:
        subprocess.run(["pdflatex", tex_file], stdout=devnull, stderr=devnull, check=True)

    for ext in [".log", ".aux", ".out"]:
        aux_file = tex_file.replace(".tex", ext)
        if os.path.exists(aux_file):
            os.remove(aux_file)
    
    print('PDF generated.')


def call_LLM(final_prompt: str):
    print('calling LLM...')

    client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-R1",
        messages=
            [
                {
                    "role": "user",
                    "content": final_prompt
                }
            ],
        temperature=0.5,
        top_p=0.5,
        top_k=30,
        max_tokens=4000,
        repetition_penalty=1,
    )

    content = response.choices[0].message.content

    print(f"COT: {content.split('</think>')[0]}")
    return content.split("</think>")[1]


if __name__ == "__main__":
    prompt = resume_prompt_builder('Master_Resume.tex', 'prompt.txt', 'job_desc.txt')
    # print(prompt)
    latex_styling = read_file('Master_Resume.tex').split("%%%%%%  RESUME STARTS HERE  %%%%%%")[0]
    # generated_resume = read_file('main.tex').split("%%%%%%  RESUME STARTS HERE  %%%%%%")[1]

    # # typical token count 7778 in | 2793 out
    generated_resume = call_LLM(prompt)
    generate_pdf(latex_styling + generated_resume)

    applications_dir = "applications"
    os.makedirs(applications_dir, exist_ok=True)

    company_job_role = input("Enter the company and job role: ")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    app_folder = os.path.join(applications_dir, f"{company_job_role} - {timestamp}")
    os.makedirs(app_folder, exist_ok=True)

    shutil.copy("job_desc.txt", os.path.join(app_folder, "job_desc.txt"))
    shutil.move("resume.tex", os.path.join(app_folder, "resume.tex"))
    print(f"Application saved in: {app_folder}")