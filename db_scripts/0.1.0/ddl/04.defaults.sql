ALTER TABLE ONLY payment_list ALTER COLUMN id SET DEFAULT nextval('payment_list_id_seq'::regclass);
