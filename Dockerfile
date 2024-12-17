FROM python:3.9
LABEL authors="Sofia.Petrenko"

WORKDIR /csai_question_answering_bot
ENV PYTHONPATH=/csai_question_answering_bot

ENV TRANSFORMERS_CACHE=/csai_question_answering_bot/.cache/huggingface
ENV HF_HOME=/csai_question_answering_bot/.cache/huggingface
RUN mkdir -p $TRANSFORMERS_CACHE && chmod -R 777 $TRANSFORMERS_CACHE

RUN chown 33:33 . && chmod -R 777 .

EXPOSE 8080

USER 33

COPY --chown=33:33 requirements.txt requirements.txt
RUN python -m venv venv && \
    venv/bin/pip install --upgrade pip && \
    venv/bin/pip install -r requirements.txt

COPY --chown=33:33 src src

CMD ["/bin/bash", "-c", "source venv/bin/activate && python src/tg_bot/main.py"]
